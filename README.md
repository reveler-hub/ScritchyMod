# ScritchyMod

Fan-made [MelonLoader](https://melonwiki.xyz/) mods for Scritchy Scratchy that read and act on real game state.

**This is an unofficial project, not affiliated with or endorsed by Lunch Money Games.** It doesn't distribute any of the game's own files — the mods build against interop assemblies MelonLoader generates locally on your own machine from your own game install.

## What's here

### `Mods/` — MelonLoader mods, require MelonLoader installed in the game
- **ScritchyOverlay** — draws a colored marker over each currently-winning slot's real on-screen position: green for a normal win, yellow for the ticket's own top-value ("jackpot") symbol, blue for the universal Super Jackpot symbol.
- **Jackpot** — press **J** to set every slot on the focused ticket to that ticket type's own jackpot symbol. A test/cheat tool, not meant for legitimate play.
- **AutoScratch** — press **S** to reveal only the currently-winning slots on the focused ticket once; press **A** to toggle continuous auto-reveal of winning slots as you focus new tickets.

<img width="373" height="321" alt="github_green" src="https://github.com/user-attachments/assets/527413b4-0d67-4aff-9b82-3b60eaf89855" />
<img width="419" height="320" alt="mini_github_jackpot" src="https://github.com/user-attachments/assets/2e3399c7-57ac-4250-8e51-17059e064157" />



## Setup

1. **Install MelonLoader** into your game folder: download a release from [github.com/LavaGang/MelonLoader](https://github.com/LavaGang/MelonLoader) (the plain `MelonLoader.x64.zip`, not the installer), and extract `version.dll` + the `MelonLoader/` folder directly into your Scritchy Scratchy install directory (next to `ScritchyScratchy.exe`).
2. **Run the game once** with MelonLoader installed. On first launch it generates real C# interop assemblies for the game's own classes under `MelonLoader/Il2CppAssemblies/` — this can take a few minutes. Let it finish; if it seems to hang for an unusually long time with near-zero CPU use, it's likely genuinely stuck — closing and relaunching once has resolved this every time it's happened.
3. **Build a mod**: set the `SCRITCHY_GAME_DIR` environment variable to your game's install folder, then build:
   ```
   export SCRITCHY_GAME_DIR="/path/to/Scritchy Scratchy"
   cd Mods/ScritchyOverlay && dotnet build
   ```
   (Repeat per mod, or per folder as needed. Requires the .NET SDK.)
4. **Install the mod**: copy the built `.dll` (in `bin/Debug/net6.0/`) into `Mods/` at your game's *root* — not nested inside the `MelonLoader/` folder. MelonLoader creates this folder itself on first run.
5. Launch the game normally through Steam.

## Two environment gotchas (Wine/Proton specifically)

If you're extending these mods, two things bit us during development that are worth knowing up front:

- **Legacy `UnityEngine.Input` doesn't work in this game** — calling `Input.GetKeyDown` throws a native exception every frame and can destabilize the game. This game uses Unity's newer Input System package instead. Use `UnityEngine.InputSystem.Keyboard.current` (e.g. `Keyboard.current.jKey.wasPressedThisFrame`), as all three mods here do.
- **Legacy IMGUI (`OnGUI`, `GUI.Label`, `GUI.DrawTexture`) triggers a known Wine/Proton + Unity bug** that freezes the game while alt-tab is held. The base game never uses legacy IMGUI, so this stays dormant unless a mod wakes it up. `ScritchyOverlay` avoids this entirely by drawing through a real `Canvas` + `TextMeshProUGUI`, the same way the game's own UI works — do the same rather than reaching for `OnGUI`.

More generally: before calling an engine API from a mod, it's worth a quick check (e.g. reading method names/visibility straight from `MelonLoader/Il2CppAssemblies/Assembly-CSharp.dll`'s metadata) that the base game actually exercises that code path itself. Unity strips unused methods from IL2CPP builds, and APIs the game never touches internally can be missing or broken even though the interop assembly still declares them.

## License

MIT — see [LICENSE](LICENSE).
