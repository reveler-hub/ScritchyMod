#!/usr/bin/env python3
import sys, re, struct, time, os, bisect
import numpy as np
from Ticket_layouts import SHAPES, TEMPLATES

PID = None
TICKET_KLASS = 0x3192f0d0
POLL_SECONDS = 5.0
mem_path = None
maps_path = None

def find_game_pid():
    # Match on argv[0] specifically, not just "the exe name appears somewhere
    # in the command line" — Steam's launch chain (reaper, bwrap, the Proton
    # python wrapper, Wine's internal steam.exe shim) all mention the game's
    # path as a later argument while launching something else as argv[0].
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/cmdline", "rb") as f:
                argv0 = f.read().split(b"\0", 1)[0].decode(errors="replace")
        except OSError:
            continue
        name = argv0.replace("\\", "/").rsplit("/", 1)[-1].lower()
        if name == "scritchyscratchy.exe":
            return entry
    return None

def configure(pid, klass=0x3192f0d0, poll=5.0):
    global PID, TICKET_KLASS, POLL_SECONDS, mem_path, maps_path
    PID = pid
    TICKET_KLASS = klass
    POLL_SECONDS = poll
    mem_path = f"/proc/{PID}/mem"
    maps_path = f"/proc/{PID}/maps"

def render_template(template, slot_positions, slots, winners, penalties):
    lines = list(template)
    for idx, (row, cs, ce) in slot_positions.items():
        if idx >= len(slots) or slots[idx] is None:
            continue
        _, _, symbol, needed, value = slots[idx]
        if symbol in winners:
            text = "***"
        elif symbol in penalties:
            text = "xxx"
        else:
            text = "."
        span = ce - cs
        pad = (span - len(text)) // 2
        l = lines[row]
        lines[row] = l[:cs + pad] + text + l[cs + pad + len(text):ce] + l[ce:]
    return lines

def render_shape(shape_rows, slots, winners, penalties):
    cell_w = 8
    max_cols = max(len(row) for row in shape_rows)
    lines = []
    for row in shape_rows:
        pad = " " * (((max_cols - len(row)) * cell_w) // 2)
        cells = []
        for idx in row:
            if idx is None:
                cells.append(" " * cell_w)
                continue
            s = slots[idx] if idx < len(slots) else None
            if s is None:
                cells.append(" " * cell_w)
                continue
            _, _, symbol, needed, value = s
            if symbol in winners:
                text = "***"
            elif symbol in penalties:
                text = "xxx"
            else:
                text = "."
            cells.append(text.center(cell_w))
        lines.append(pad + "".join(cells))
        lines.extend([""] * 3)  # vertical gap between rows
    return lines[:-3]  # drop trailing gap after the last row

def get_rw_regions():
    regions = []
    with open(maps_path) as f:
        for line in f:
            m = re.match(r'([0-9a-f]+)-([0-9a-f]+) (\S+)', line)
            if not m:
                continue
            start, end, perms = m.group(1), m.group(2), m.group(3)
            if perms.startswith('rw'):
                regions.append((int(start, 16), int(end, 16)))
    return regions

def read(mem, addr, size):
    try:
        mem.seek(addr)
        return mem.read(size)
    except (ValueError, OverflowError) as e:
        raise OSError(str(e))

def try_decode_string(mem, ptr):
    if ptr < 0x10000:
        return None
    try:
        hdr = read(mem, ptr, 24)
    except OSError:
        return None
    if len(hdr) < 24:
        return None
    klass_ptr, monitor, length = struct.unpack_from('<QQi', hdr, 0)
    if not (0 <= length <= 200) or klass_ptr < 0x10000 or monitor > 0x10000:
        return None
    try:
        chars = read(mem, ptr + 20, length * 2 + 2)
    except OSError:
        return None
    if len(chars) < length * 2 + 2 or chars[-2:] != b'\x00\x00':
        return None
    try:
        return chars[:-2].decode('utf-16-le')
    except UnicodeDecodeError:
        return None

def find_ticket_objects(mem, regions):
    hits = []
    for rstart, rend in regions:
        size = rend - rstart
        try:
            mem.seek(rstart)
            buf = mem.read(size)
        except OSError:
            continue
        if not buf:
            continue
        n = (len(buf) // 8) * 8
        if n == 0:
            continue
        arr = np.frombuffer(buf, dtype='<u8', count=n // 8)
        for off in np.nonzero(arr == TICKET_KLASS)[0]:
            hits.append(rstart + int(off) * 8)
    return hits

def collect_tickets(mem, hits):
    tickets = []
    seen = set()
    for h in hits:
        t = read_ticket(mem, h)
        if t and t["obj"] not in seen:
            seen.add(t["obj"])
            tickets.append(t)
    return tickets

def region_starts_for_hits(hits, regions):
    starts = sorted(r[0] for r in regions)
    result = set()
    for h in hits:
        i = bisect.bisect_right(starts, h) - 1
        if i >= 0:
            result.add(starts[i])
    return result

def get_jackpot_symbol(mem, ticketdata_ptr):
    # The ticket type's own top-value symbol (excluding "Super Jackpot", which
    # is a separate universal bonus, not one of this ticket's regular tiers).
    try:
        td_blob = read(mem, ticketdata_ptr, 0x50)
        syms_list, = struct.unpack_from('<Q', td_blob, 0x48)
        list_hdr = read(mem, syms_list, 0x20)
        items_ptr, size, _ = struct.unpack_from('<Qii', list_hdr, 0x10)
        if not (0 < size < 32):
            return None
        sym_ptrs = struct.unpack_from(f'<{size}Q', read(mem, items_ptr, 0x20 + size * 8), 0x20)
    except OSError:
        return None

    best_id, best_val = None, None
    for sp in sym_ptrs:
        try:
            d = read(mem, sp, 0x28)
            sid = try_decode_string(mem, struct.unpack_from('<Q', d, 0x18)[0])
            val, = struct.unpack_from('<d', d, 0x20)
        except OSError:
            continue
        if sid is None or sid == "Super Jackpot":
            continue
        if best_val is None or val > best_val:
            best_id, best_val = sid, val
    return best_id

def read_ticket(mem, obj_start):
    blob = read(mem, obj_start, 0xE0)
    if len(blob) < 0xE0:
        return None
    cached_ptr, = struct.unpack_from('<Q', blob, 0x10)
    if cached_ptr == 0:
        return None  # Unity destroyed this GameObject; stale managed object still in heap

    symbolSlots_ptr, = struct.unpack_from('<Q', blob, 0x98)
    ticketdata_ptr, = struct.unpack_from('<Q', blob, 0xC8)
    allScratched = blob[0xD1]
    isJackpot = blob[0xD2]

    if not (0x10000 < symbolSlots_ptr < 0x7fffffffffff):
        return None

    name = None
    jackpot_symbol = None
    if ticketdata_ptr > 0x10000:
        try:
            td_blob = read(mem, ticketdata_ptr, 0x20)
            id_ptr, = struct.unpack_from('<Q', td_blob, 0x10)
            name = try_decode_string(mem, id_ptr)
        except OSError:
            pass
        jackpot_symbol = get_jackpot_symbol(mem, ticketdata_ptr)

    try:
        list_hdr = read(mem, symbolSlots_ptr, 0x20)
        items_ptr, size, version = struct.unpack_from('<Qii', list_hdr, 0x10)
    except OSError:
        return None
    if not (0 < size < 32):
        return None

    try:
        arr = read(mem, items_ptr, 0x20 + size * 8)
        slot_ptrs = struct.unpack_from(f'<{size}Q', arr, 0x20)
    except OSError:
        return None

    slots = []
    for sp in slot_ptrs:
        if sp < 0x10000:
            slots.append(None)
            continue
        try:
            slot_blob = read(mem, sp, 0x110)
        except OSError:
            slots.append(None)
            continue
        is_scratched = slot_blob[0xC8]
        scratch_pct, = struct.unpack_from('<f', slot_blob, 0x104)
        data_ptr, = struct.unpack_from('<Q', slot_blob, 0xD0)
        symbol = None
        count_needed = None
        value = None
        if data_ptr > 0x10000:
            try:
                data_blob = read(mem, data_ptr, 0x38)
                id_ptr, = struct.unpack_from('<Q', data_blob, 0x18)
                value, = struct.unpack_from('<d', data_blob, 0x20)
                count_needed, = struct.unpack_from('<i', data_blob, 0x28)
                symbol = try_decode_string(mem, id_ptr)
            except OSError:
                pass
        slots.append((bool(is_scratched), scratch_pct, symbol, count_needed, value))

    counts = {}
    for s in slots:
        if s is None:
            continue
        _, _, symbol, count_needed, value = s
        if symbol is None:
            continue
        c = counts.setdefault(symbol, {"count": 0, "needed": count_needed, "value": value})
        c["count"] += 1

    matched = [sym for sym, c in counts.items() if c["needed"] is not None and c["count"] >= c["needed"]]
    winners = [sym for sym in matched if counts[sym]["value"] is not None and counts[sym]["value"] > 0]
    penalties = [sym for sym in matched if counts[sym]["value"] is not None and counts[sym]["value"] < 0]
    # value == 0 is neither: a matched-but-worthless symbol stays neutral ("."), not a penalty

    return {
        "obj": obj_start,
        "name": name,
        "allScratched": bool(allScratched),
        "isJackpot": bool(isJackpot),
        "slots": slots,
        "counts": counts,
        "winners": winners,
        "penalties": penalties,
        "jackpot_symbol": jackpot_symbol,
    }

def render(tickets, scan_kind="full"):
    print("\033[H\033[2J\033[3J", end="")  # cursor home + clear screen/scrollback, no subprocess
    print(f"=== Scritchy Scratchy live ticket viewer (pid {PID}) ===  {time.strftime('%H:%M:%S')}  [{scan_kind} scan]\n")
    if not tickets:
        print("(no live ticket objects found)")
        sys.stdout.flush()
        return
    for t in tickets:
        print(f"Ticket: {t['name'] or '???'}")
        slots = t['slots']
        shape = SHAPES.get(t['name'])
        template_info = TEMPLATES.get(t['name'])

        template_ok = template_info and len(slots) == template_info[2]
        always_show = template_ok and template_info[3]
        drew_shape = False

        if template_ok and (t["winners"] or (always_show and t["penalties"])):
            template, slot_positions, _, _ = template_info
            for line in render_template(template, slot_positions, slots, t["winners"], t["penalties"]):
                print("    " + line)
            drew_shape = True
        elif t["winners"] and shape:
            for line in render_shape(shape, slots, t["winners"], t["penalties"]):
                print("    " + line)
            drew_shape = True

        if not t["winners"] and not drew_shape:
            print("    No Win")
        else:
            # "Jackpot" means the winning symbol is this ticket type's own
            # highest-value tier (or the universal "Super Jackpot" symbol) —
            # not just any win. A win on a lower tier shows only the art.
            if "Super Jackpot" in t["winners"]:
                label, target = "Super Jackpot", "Super Jackpot"
            elif t["jackpot_symbol"] in t["winners"]:
                label, target = "Jackpot", t["jackpot_symbol"]
            else:
                label = None
            if label:
                positions = [f"slot{i}" for i, s in enumerate(slots) if s is not None and s[2] == target]
                print(f"    {label} --> {', '.join(positions)}")
        print()
    sys.stdout.flush()

def main():
    auto_pid = len(sys.argv) <= 1
    if not auto_pid:
        pid = sys.argv[1]
    else:
        pid = find_game_pid()
        if pid is None:
            print("Could not find a running ScritchyScratchy.exe process.")
            sys.exit(1)
        print(f"Auto-detected game PID: {pid}")

    klass = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x3192f0d0
    poll = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
    configure(pid, klass, poll)
    mem = open(mem_path, 'rb')
    known_starts = None  # region start addresses that held ticket objects last time

    while True:
        t_start = time.time()
        try:
            regions = get_rw_regions()
            tickets = []
            full_scan_done = False

            if known_starts:
                fast_regions = [r for r in regions if r[0] in known_starts]
                hits = find_ticket_objects(mem, fast_regions)
                tickets = collect_tickets(mem, hits)

            if not tickets:
                # cache miss (first run, or ticket moved/appeared in a new region): full scan
                hits = find_ticket_objects(mem, regions)
                tickets = collect_tickets(mem, hits)
                full_scan_done = True
                known_starts = region_starts_for_hits(hits, regions) if hits else None

            render(tickets, scan_kind="full" if full_scan_done else "fast")

        except OSError:
            print(f"\nGame process (pid {pid}) is no longer accessible (closed/crashed?).")
            if not auto_pid:
                print("Exiting. Re-run without a PID argument to enable auto-reconnect on restart.")
                sys.exit(1)
            print("Waiting for it to restart...")
            sys.stdout.flush()
            new_pid = None
            while new_pid is None:
                time.sleep(2)
                new_pid = find_game_pid()
            pid = new_pid
            print(f"Reconnected to new game PID: {pid}")
            configure(pid, klass, poll)
            mem = open(mem_path, 'rb')
            known_starts = None
            continue

        elapsed = time.time() - t_start
        time.sleep(max(0.0, poll - elapsed))

if __name__ == "__main__":
    main()
