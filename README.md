# FPV-Simulator-Video-Filter
This is a Windows tool that captures the live-feed from an FPV-Simulator and applies a real-time analog-style video filter (scanlines, noise,glitches,signal loss, chromatic aberration), and forwards mouse clicks through to the simulator.<br>
All from a resizable window that goes to even borderless-fullscreen with **F** for the best user experience. <br>
It also has a settings menu in which all the effects can be changed, customized or presets chosen. <br>
When closing the tool, a settings backup of the new changed one will be saved and automatically restored after reopening. <br>
It also saves the last Simulator it was used with and chooses it directly when opened.<br>
The tool also allows screenshots and screen recordings to be made directly using **S** or **R**.

<img src="https://cdn.hackclub.com/01a030ce-5f82-76e8-a306-491d9094d616/Screenshot%202026-08-24%20014501.png" width="100%" height="100%" alt="Boat" >

## Run Program
### To run the Python File
To open the program open a **Terminal** in the folder and and run ```python video_filter.py```<br>
Then select the wanted window by typing in the number in front of it and and then **Press Enter**

<img src="https://cdn.hackclub.com/01a0310d-bbc1-722e-be13-b0eb745e42aa/Select%20Window.png" width="80%" height="80%" alt="Select Window" >


### To create the .exe file (if needed)
Open **PowerShell** and change to the folder where the **video_filter.py** and **fpv_icon.ico** files are saved. 
<img src="https://cdn.hackclub.com/01a03120-68b2-76b2-b2d9-86669e3f9f52/Move%20to%20Folder.png" width="80%" height="80%" alt="Move to Folder" >
Then type **pyinstaller --onefile --icon=fpv_icon.ico --add-data "fpv_icon.ico;." video_filter.py**
<img src="https://cdn.hackclub.com/01a03120-8814-7663-86f8-6136695f0cc8/Create%20.exe.png" width="100%" height="100%" alt="Create .exe" >

## Settings Menu
The settings menu allows the changing of the following with sliders:<br>
**Noise/Scanline Strength/Scanline Speed/Scanline Spacing/Glitch Chance/Signal Loss Chance/Bad Signal Chance/Chromatic Aberration**<br>
The settings menu is available in **English and German**:
| English Version | German Version |
| --------------- | -------------- |
| <img src="https://cdn.hackclub.com/01a030d4-b7e9-744e-8f4d-eb1fdad48bbb/Screenshot%202026-08-24%20014517.png" width="100%" height="100%" alt="English Settings Version" > | <img src="https://cdn.hackclub.com/01a030d4-e0b0-78a1-9fc6-c318b22b936d/Screenshot%202026-08-24%20014523.png" width="100%" height="100%" alt="German Settings Version" > |

**Hotkeys**:<br>
**F** = Switches between borderless fullscreen and windowed<br>
**S** = Takes Screenshots<br>
**R** = Starts/Stops Recording<br>
**Q** = Quits the Program<br>



<img src="https://cdn.hackclub.com/01a030fc-47e7-7e07-a36a-259b577501e1/Run%20Python%20Program.png" width="80%" height="80%" alt="Run Python Program" ><br>
