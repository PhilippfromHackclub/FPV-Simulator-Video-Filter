# FPV-Simulator-Video-Filter
This is a Windows tool that captures the live-feed from an FPV-Simulator and applies a real-time analog-style video filter (scanlines, noise,glitches,signal loss, chromatic aberration), and forwards mouse clicks through to the simulator.<br>
All from a resizable window that goes to even borderless-fullscreen with ``F`` for the best user experience. <br>
It also has a settings menu in which all the effects can be changed, customized or presets chosen. <br>
When closing the tool, a settings backup of the new changed one will be saved and automatically restored after reopening. <br>
It also saves the last Simulator it was used with and chooses it directly when opened.<br>
The tool also allows screenshots and screen recordings to be made directly using ``S`` or ``R``.

The tool was built to recreate the analog look and get one used to the scanlines and glitches while practicing.

<img src="https://cdn.hackclub.com/01a030ce-5f82-76e8-a306-491d9094d616/Screenshot%202026-08-24%20014501.png" width="100%" height="100%" alt="Video Filter" >

## Features
+ **Live window capture** — automatically lists all open windows and captures the selected one via the `**Windows Graphics Capture API** (``windows-capture``), with no manual window-title typing required.
+ **Click-through** — left clicks in the live-feed window are forwarded to the simulator at the correct scaled coordinates, so interacting with menus is still possible without switching windows.
+ **Real-time analog video filter**
  + Animated scanlines (adjustable spacing, strenght, and scroll speed)
  + Film-grain style noise
  + Random thick "tracking error" glitch bars
  + Occasional full signal-loss overlay ("NO SIGNAL")
  + "Bad signal" effect — every line is shifted, image stays visible
  + Chromatic aberrration (RGB channel offset)
+ **In-app settings panel** — custom-drawn sliders (no native OS trackbar limitations) for every filter parameter, with a visible drag handle.
+ **Presets** — one-click "Standard", "Clean", "Old CRT", and "Extremely Trashed" presete that set all sliders at once.
+ **Bilingual UI** — toggle between German and English directly from a clickable button in the settings panel.
+ **Recording** — press ``R`` to start/stop saving the filtered /feed as an ``.mp4``, ``S`` to save a ``.png`` screenshot.
+ **Persistent settings** — slider values, language, and the last-used simulator window are saved to ``einstellungen.json`` and restored automatically on the next launch (including auto-selecting the last window if it's still open).
+ **Borderless fullscreen toogle** — press``F`` to switch the preview window to true borderless fullscreen.
+ **Automatic window icon** — the preview window inherits the simulator's own icon where possible, with a generated fallback icon.

| Settings English | Settings German |
| ---------------- | --------------- |
<img src="https://cdn.hackclub.com/01a03197-04c6-7f21-9776-951e96024f2d/Settings_English.png" width="100%" height="100%" alt="Settings English" > | <img src="https://cdn.hackclub.com/01a03197-2604-7d76-8995-5d35d0ca545f/Settings_German.png" width="100%" height="100%" alt="Settings German" >

## Requirements
+ **Windows 10/11**
+ **Python 3.10+**
+ **Dependencies:**

``pip install opencv-python pydirectinput py32 windows-capture pillow``

## Usage
1. Run the script(or the built .exe, see below):
   ``python video_filter.py
2. A console window lists all currently open window. Enter the number of the simulator window chosen to capture (or it will be auto-selected if it matches your last session).
3. A live-feed window opens, alongside an Einstellungen(Settings) window with sliders for every filter effect.
4. Adjust filters live, pick presets, or switch language directly in the settings window.
   
## Keyboard controls (live-feed window focused)
**F** = Switches between borderless fullscreen and windowed<br>
**S** = Takes Screenshots<br>
**R** = Starts/Stops Recording<br>
**Q** = Quits the Program<br>
Left-clicking inside the live-feed window forwards the click to the simulator at the correct scaled position.


## Building a standalone .exe
No Python installation required for end users — package it with PyInstaller:<br>
``pip install pyinstaller``<br>
``pyinstaller --onefile --icon=fpv_icon.ico --add-data "fpv_icon.ico;." video_filter.py``<br>
The resulting ``video_filter.exe``(in ``dist/``) is fully self-contained. Settings, recordings, and screenshots are saved next to the ``.exe`` itself, not in a temp folder.<br>
>[!Note]
>Note: a console window is intentionally kept ( no ``-- noconsole``)<br>
>since window selection happanes via a text prompt.<br>

## Platform support
This tool is Windows-only. It relies on the **Windows Graphics Capture API** (``windows-capture``), ``pywin32`` (windoe/icon handling), and ``pydirectinput`` (click forwarding) — none of which have macOS/Linux equivalents (to my knolage). A cross-platform version would require a substantial rewrite using platform_native capture and input APIs.
