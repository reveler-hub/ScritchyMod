using System.Collections.Generic;
using MelonLoader;
using UnityEngine;
using UnityEngine.InputSystem;
using Il2Cpp;

[assembly: MelonInfo(typeof(AutoScratchMod.AutoScratchMod), "AutoScratch", "0.1.0", "test")]
[assembly: MelonGame(null, null)]

namespace AutoScratchMod
{
    // S = reveal (only) the currently-winning slots on the focused ticket, once.
    // A = toggle continuous auto-reveal of winning slots while a ticket is focused.
    // Uses the game's own public SymbolSlot.Reveal() method (not a raw memory
    // write) and the New Input System (Keyboard.current), since the legacy
    // Input class crashed here — this game doesn't use it internally.
    public class AutoScratchMod : MelonMod
    {
        private bool autoScratchEnabled;
        private bool suppressErrors;
        private float lastAutoScratchCheck;

        public override void OnInitializeMelon()
        {
            MelonLogger.Msg("AutoScratch mod loaded. S = reveal winning slots. A = toggle auto-reveal.");
        }

        private static HashSet<string> GetWinningSymbolIds(Ticket ticket)
        {
            var result = new HashSet<string>();
            if (ticket == null || ticket.Symbols == null) return result;

            var counts = new Dictionary<string, int>();
            var neededById = new Dictionary<string, int>();
            var valueById = new Dictionary<string, double>();
            foreach (var slot in ticket.Symbols)
            {
                if (slot == null || slot.Data == null) continue;
                var d = slot.Data;
                counts.TryGetValue(d.id, out int c);
                counts[d.id] = c + 1;
                neededById[d.id] = d.countNeeded;
                valueById[d.id] = d.value;
            }
            foreach (var kv in counts)
            {
                if (neededById.TryGetValue(kv.Key, out int need) && kv.Value >= need &&
                    valueById.TryGetValue(kv.Key, out double val) && val > 0)
                {
                    result.Add(kv.Key);
                }
            }
            return result;
        }

        private static void RevealWinningSlots(Ticket ticket, bool verbose)
        {
            if (ticket == null || ticket.Symbols == null || ticket.Data == null) return;
            var winners = GetWinningSymbolIds(ticket);
            if (winners.Count == 0)
            {
                if (verbose) MelonLogger.Msg($"Ticket '{ticket.Data.id}': no winning symbols right now.");
                return;
            }

            int revealed = 0;
            foreach (var slot in ticket.Symbols)
            {
                if (slot == null || slot.Data == null) continue;
                if (slot.IsScratched) continue;
                if (!winners.Contains(slot.Data.id)) continue;
                slot.Reveal();
                revealed++;
            }
            if (verbose)
                MelonLogger.Msg(revealed > 0
                    ? $"Revealed {revealed} winning slot(s) on '{ticket.Data.id}'."
                    : $"Ticket '{ticket.Data.id}': winning slots already revealed.");
        }

        public override void OnUpdate()
        {
            bool sPressed = false, aPressed = false;
            try
            {
                var kb = Keyboard.current;
                if (kb != null)
                {
                    sPressed = kb.sKey.wasPressedThisFrame;
                    aPressed = kb.aKey.wasPressedThisFrame;
                }
            }
            catch (System.Exception ex)
            {
                if (!suppressErrors)
                {
                    MelonLogger.Error("Keyboard.current check itself threw: " + ex);
                    suppressErrors = true;
                }
                return;
            }

            if (aPressed)
            {
                autoScratchEnabled = !autoScratchEnabled;
                MelonLogger.Msg("Auto-reveal winning slots: " + (autoScratchEnabled ? "ENABLED" : "disabled"));
            }

            bool doAutoCheck = false;
            if (autoScratchEnabled)
            {
                float now = Time.realtimeSinceStartup;
                if (now - lastAutoScratchCheck > 0.2f)
                {
                    lastAutoScratchCheck = now;
                    doAutoCheck = true;
                }
            }

            if (!sPressed && !doAutoCheck) return;

            try
            {
                var tickets = UnityEngine.Object.FindObjectsOfType<Ticket>();
                if (sPressed && tickets.Length == 0) MelonLogger.Msg("No live ticket found.");
                foreach (var ticket in tickets)
                    RevealWinningSlots(ticket, verbose: sPressed);
            }
            catch (System.Exception ex)
            {
                MelonLogger.Error("Scratch handler threw: " + ex);
            }
        }
    }
}
