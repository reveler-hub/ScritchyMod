using System.Collections.Generic;
using MelonLoader;
using UnityEngine;
using Il2CppTMPro;
using Il2Cpp;

[assembly: MelonInfo(typeof(ScritchyOverlay.OverlayMod), "ScritchyOverlay", "0.4.0", "test")]
[assembly: MelonGame(null, null)]

namespace ScritchyOverlay
{
    // Uses a real Canvas + TextMeshProUGUI pool instead of OnGUI/legacy IMGUI.
    // OnGUI triggers a known Wine/Proton + Unity bug where alt-tab freezes the
    // game; the base game never touches legacy IMGUI itself (it's all Canvas/TMP),
    // so building the overlay the same way avoids waking up that code path at all.
    public class OverlayMod : MelonMod
    {
        private const int PoolSize = 12;

        private static readonly Color WinColor = Color.green;
        private static readonly Color JackpotColor = Color.yellow;
        private static readonly Color SuperJackpotColor = new Color(0.2f, 0.6f, 1f);

        private struct Marker
        {
            public float X, Y;
            public Color Color;
        }

        private Canvas canvas;
        private readonly List<TextMeshProUGUI> pool = new List<TextMeshProUGUI>();
        private readonly List<Marker> markers = new List<Marker>();
        private float lastLogTime;
        private float lastComputeTime;

        public override void OnInitializeMelon()
        {
            var canvasGO = new GameObject("ScritchyOverlayCanvas");
            UnityEngine.Object.DontDestroyOnLoad(canvasGO);
            canvas = canvasGO.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 1000;

            for (int i = 0; i < PoolSize; i++)
            {
                var go = new GameObject($"Marker{i}");
                go.transform.SetParent(canvasGO.transform, false);
                var tmp = go.AddComponent<TextMeshProUGUI>();
                tmp.text = "▼";
                tmp.fontSize = 48;
                tmp.alignment = TextAlignmentOptions.Center;
                tmp.rectTransform.sizeDelta = new Vector2(80, 80);
                go.SetActive(false);
                pool.Add(tmp);
            }

            MelonLogger.Msg("ScritchyOverlay loaded (Canvas/TMP overlay).");
        }

        private static string GetJackpotSymbol(TicketData data)
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

        private static Camera GetCamera()
        {
            return Camera.main != null ? Camera.main : UnityEngine.Object.FindObjectOfType<Camera>();
        }

        public override void OnUpdate()
        {
            float now = Time.realtimeSinceStartup;
            if (now - lastComputeTime < 0.1f) return;
            lastComputeTime = now;

            markers.Clear();

            var cam = GetCamera();
            if (cam == null)
            {
                ApplyMarkers();
                return;
            }

            bool doLog = now - lastLogTime > 2f;
            if (doLog) lastLogTime = now;

            var tickets = UnityEngine.Object.FindObjectsOfType<Ticket>();
            foreach (var ticket in tickets)
            {
                if (ticket == null || ticket.Symbols == null) continue;
                var slots = ticket.Symbols;

                var counts = new Dictionary<string, int>();
                var neededById = new Dictionary<string, int>();
                var valueById = new Dictionary<string, double>();
                foreach (var slot in slots)
                {
                    if (slot == null || slot.Data == null) continue;
                    var d = slot.Data;
                    counts.TryGetValue(d.id, out int c);
                    counts[d.id] = c + 1;
                    neededById[d.id] = d.countNeeded;
                    valueById[d.id] = d.value;
                }

                string jackpotSymbol = GetJackpotSymbol(ticket.Data);

                for (int i = 0; i < slots.Count; i++)
                {
                    var slot = slots[i];
                    if (slot == null || slot.Data == null) continue;
                    var d = slot.Data;

                    bool matched = counts.TryGetValue(d.id, out int cnt) && neededById.TryGetValue(d.id, out int need) && cnt >= need;
                    bool isWinner = matched && valueById.TryGetValue(d.id, out double val) && val > 0;
                    if (!isWinner) continue;

                    Color color;
                    if (d.id == "Super Jackpot") color = SuperJackpotColor;
                    else if (d.id == jackpotSymbol) color = JackpotColor;
                    else color = WinColor;

                    Vector3 world = slot.transform.position;
                    Vector3 screen = cam.WorldToScreenPoint(world);
                    if (screen.z < 0) continue;

                    if (doLog)
                        MelonLogger.Msg($"  slot{i} id={d.id} color={color} screen=({screen.x:F0},{screen.y:F0})");

                    markers.Add(new Marker { X = screen.x, Y = screen.y, Color = color });
                }
            }

            ApplyMarkers();
        }

        private void ApplyMarkers()
        {
            for (int i = 0; i < pool.Count; i++)
            {
                var tmp = pool[i];
                if (i < markers.Count)
                {
                    var m = markers[i];
                    // ScreenSpaceOverlay canvases use the same bottom-left-origin
                    // screen coordinates as WorldToScreenPoint — no Y-flip needed
                    // (unlike OnGUI's top-left-origin coordinate space).
                    tmp.rectTransform.position = new Vector3(m.X, m.Y + 60f, 0f);
                    tmp.color = m.Color;
                    if (!tmp.gameObject.activeSelf) tmp.gameObject.SetActive(true);
                }
                else if (tmp.gameObject.activeSelf)
                {
                    tmp.gameObject.SetActive(false);
                }
            }
        }
    }
}
