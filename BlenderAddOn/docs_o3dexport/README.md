# O3DEXPORT
Blender 4.2 Add-On to export scenes to O3DE.
Textures, Materials, Meshes and the Object hierarchy.

# YouTube Tutorial
TBD

# How To Use
## Long Story Short
#### 2. Install O3DEXPORT as a Blender AddOn
- Download the script as a ZIP file.
- Open Blender. Menu option Edit --> Preferences
- Click *Add-ons* button.
- Click *Install an add-on* button.
- select the ZIP file.
The O3DEXPORT plugin is located inside the "3D Viewport" as a Panel in the Properties region (Press N Key). You should see a tab named *O3DEXPORT* next to *View*, *Tool* and *Item* tabs.

## Debugging O3DEXPORT with vscode (For Developers)
1. Install the extension named `Blender Development` by Jacques Lucke.
2. In vscode install bpy.types symbols:  `python -m pip install fake-bpy-module-latest`
3. In vscode install PIL via pillow module:  `python -m pip install pillow`
4. In vscode settings for `Blender Development` extend the `PYTHONPATH` so
python finds the modules of this add-on:
```json
...
    "blender.addon.reloadOnSave": true,
    "blender.environmentVariables": {

        "PYTHONPATH": "%PYTHONPATH%;C:\\GIT\\o3dimport\\BlenderAddOn\\o3dexport"
    }
...
```
In the example above change `C:\\GIT\\o3dimport\\BlenderAddOn\\o3dexport` according to your needs.
Also I suggest to use the setting `"blender.addon.reloadOnSave": true,`

4. You must start blender from vscode using this addon with "Ctrl+Shift+P", type `Blender` and start it.
5. You can now place breakpoints and hit them when you use the add-on.


## [ OBSOLETE ] Running O3DEXPORT as a regular python script (For Developers)
If you want to modify or debug O3DEXPORT, then don't install it.
Simply clone this repository or extract the content of the ZIP file.
Let's assume you checkout/download the code at:
*C:\\path\\to\\o3dexport*

Paste the following code in the Blender Text View.
```python
import bpy
import os
import sys

projdir = "C:\\GIT\\o3dimport\\BlenderAddOn\\o3dexport"
if not projdir in sys.path:
    sys.path.append(projdir)

filename = os.path.join(projdir, "__init__.py")
exec(compile(open(filename).read(), filename, 'exec'))
```
Click the *Run Script* button. The O3DEXPORT UI will appear inside the "3D Viewport" as a Panel in the Properties region (Press N Key). You should see a tab named *O3DEXPORT* next to *View*, *Tool* and *Item* tabs.

Quick Tip to clear the 'System Console'
```python
import os
os.system('cls')
```

# How to share this script with others.
Just like any other Blender Add-On, the parent folder `o3dexport` should be compressed producing
a file named `o3dexport.zip`. Provide `o3dexport.zip` file to whoever wants to install this plugin in their
machines.
