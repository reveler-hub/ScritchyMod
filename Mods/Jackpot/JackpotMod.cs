using MelonLoader;
using UnityEngine.InputSystem;
using Il2Cpp;

[assembly: MelonInfo(typeof(JackpotMod.JackpotMod), "Jackpot", "0.2.0", "test")]
[assembly: MelonGame(null, null)]

namespace JackpotMod
{
    // Press J: set every slot on the current ticket(s) to that ticket type's
    // own jackpot-tier symbol, via the game's real SymbolSlot.UpdateData(...)
    // method (not a raw memory write), to test whether that also updates the
    // visible icon correctly (a raw Data-pointer write earlier this session
    // did not — the sprite stayed whatever was originally generated).
    // Uses the New Input System (Keyboard.current) since the legacy Input
    // class crashed here — this game doesn't use it internally.
    public class JackpotMod : MelonMod
    {
        private bool suppressErrors;

        public override void OnInitializeMelon()
        {
            MelonLogger.Msg("Jackpot mod loaded. Press J to set all slots on the current ticket to its jackpot symbol.");
        }

        private static string GetJackpotSymbolId(TicketData data)
        {
            string bestId = null;
            double bestVal = double.NegativeInfinity;
            if (data == null || data.symbols == null) return null;
            foreach (var sd in data.symbols)
            {
                if (sd == null || sd.id == "Super Jackpot") continue;
                if (sd.value > bestVal)
                {
                    bestVal = sd.value;
                    bestId = sd.id;
                }
            }
            return bestId;
        }

        private static SymbolData FindSymbolDataById(TicketData data, string id)
        {
            if (data == null || data.symbols == null) return null;
            foreach (var sd in data.symbols)
            {
                if (sd != null && sd.id == id) return sd;
            }
            return null;
        }

        public override void OnUpdate()
        {
            bool pressed;
            try
            {
                pressed = Keyboard.current != null && Keyboard.current.jKey.wasPressedThisFrame;
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
            if (!pressed) return;

            try
            {
                var tickets = UnityEngine.Object.FindObjectsOfType<Ticket>();
                int changed = 0;
                foreach (var ticket in tickets)
                {
                    if (ticket == null || ticket.Symbols == null || ticket.Data == null) continue;

                    string jackpotId = GetJackpotSymbolId(ticket.Data);
                    if (jackpotId == null) continue;
                    var jackpotData = FindSymbolDataById(ticket.Data, jackpotId);
                    if (jackpotData == null) continue;

                    foreach (var slot in ticket.Symbols)
                    {
                        if (slot == null) continue;
                        slot.UpdateData(jackpotData, ticket);
                    }

                    changed++;
                    MelonLogger.Msg($"Set all slots on '{ticket.Data.id}' to jackpot symbol '{jackpotId}'.");
                }

                if (changed == 0)
                    MelonLogger.Msg("No live ticket found.");
            }
            catch (System.Exception ex)
            {
                MelonLogger.Error("Jackpot key-handler threw: " + ex);
            }
        }
    }
}
