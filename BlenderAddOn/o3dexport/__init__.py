"""
Copyright (c) Contributors to the Open 3D Engine Project.
For complete copyright and license terms please see the LICENSE at the root of this distribution.

SPDX-License-Identifier: Apache-2.0 OR MIT
"""

# Created by Galib Arrieta (aka galibzon@github, lumbermixalot@github)
# under contract with Meta Platforms, Inc.
# Donated by Meta Platforms, Inc as an open source project.

import os
import sys
from datetime import datetime
from typing import TextIO

import bpy


bl_info = {
    "name": "O3DEXPORT: Exports scenes, meshes, materials and textures to O3DE.",
    "author": "Galib F. Arrieta",
    "version": (1, 0, 2),
    "blender": (4, 1, 0),
    "location": "3D View > UI (Right Panel) > O3DEXPORT Tab",
    "description": ("Script to export scenes, meshes, materials and textures to O3DE"),
    "warning": "",  # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "O3DE",
}


if __package__ is None or __package__ == "":
    # When running as a standalone script from Blender Text View "Run Script"
    import export_settings
    import exporter
    import fileutils
    import imageutils
    import o3material
    import scenegraph
else:
    # When running as an installed AddOn, then it runs in package mode.
    from . import (
        export_settings,
        exporter,
        fileutils,
        imageutils,
        o3material,
        scenegraph,
    )


if "bpy" in locals():
    from importlib import reload

    if "export_settings" in locals():
        reload(export_settings)
    if "exporter" in locals():
        reload(exporter)
    if "fileutils" in locals():
        reload(fileutils)
    if "o3material" in locals():
        reload(o3material)
    if "imageutils" in locals():
        reload(imageutils)
    if "scenegraph" in locals():
        reload(scenegraph)


# The following class works as namespace for some Blender String Constants that
# trigger Flake-type errors during Static Analysis.
# https://docs.blender.org/api/current/bpy_types_enum_items/property_subtype_string_items.html#rna-enum-property-subtype-string-items
class BpyPropertySubtype:
    BYTE_STRING = "BYTE_STRING"
    DIR_PATH = "DIR_PATH"
    PERCENTAGE = "PERCENTAGE"
    Z = "Z"
    Y = "Y"

    def __init__(self):
        pass


# A MessageBox utility:
def _ShowMessageBox(message: str, title: str = "O3DEXPORT", icon="INFO"):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


# https://docs.blender.org/api/current/bpy.ops.export_scene.html
VALID_AXIS_STRINGS = ("X", "Y", "Z", "-X", "-Y", "-Z")
VALID_AXIS_OPTIONS = [
    ("X", "X", ""),
    ("Y", "Y", ""),
    ("Z", "Z", ""),
    ("-X", "-X", ""),
    ("-Y", "-Y", ""),
    ("-Z", "-Z", ""),
]


def _ValidateAxisOptions(forward: str, up: str) -> bool:
    forward = forward.replace("-", "")
    up = up.replace("-", "")
    return (
        (forward != up)
        and (forward in VALID_AXIS_STRINGS)
        and (up in VALID_AXIS_STRINGS)
    )


###############################################################################
# Scene Properties
###############################################################################
def ProjectDirSet(self, value: str):
    self["projectDir"] = fileutils.GetAbsolutePathFromBlenderPath(value)


def ProjectDirGet(self) -> str:
    return self.get("projectDir", "")


class O3matPropertyGroup(bpy.types.PropertyGroup):
    """Container of options for O3DEXPORT"""

    overwriteTextures: bpy.props.BoolProperty(
        name="Overwrite Textures",
        description="If enabled, existing texture files will be overwritten",
        default=False,
    )
    overwriteMaterials: bpy.props.BoolProperty(
        name="Overwrite Materials",
        description="If enabled, existing material files will be overwritten",
        default=False,
    )
    materialsNormalFlipXChannel: bpy.props.BoolProperty(
        name="Flip X Channel",
        description="O3DE Material option for Normals: Flip X Channel",
        default=False,
    )
    materialsNormalFlipYChannel: bpy.props.BoolProperty(
        name="Flip Y Channel",
        description="O3DE Material option for Normals: Flip Y Channel. Enabled by default, because Blender uses OpenGL convention and O3DE uses DX12 convention.",
        default=True,
    )
    overwriteMeshes: bpy.props.BoolProperty(
        name="Overwrite Meshes",
        description="If enabled, existing FBX/GLTF will be overwritten",
        default=False,
    )
    overwriteSceneGraph: bpy.props.BoolProperty(
        name="Overwrite SceneGraph",
        description="If enabled, existing SGR files will be overwritten",
        default=False,
    )
    forwardAxisOption: bpy.props.EnumProperty(
        name="Forward Axis",
        description="Forward Axis",
        items=VALID_AXIS_OPTIONS,
        default=BpyPropertySubtype.Y,
    )
    upAxisOption: bpy.props.EnumProperty(
        name="Up Axis",
        description="Up Axis",
        items=VALID_AXIS_OPTIONS,
        default=BpyPropertySubtype.Z,
    )
    allowInvalidTextures: bpy.props.BoolProperty(
        name="Allow Invalid Textures",
        description="When enabled, invalid textures will be disregarded when exporting the Materials.",
        default=False,
    )
    sceneName: bpy.props.StringProperty(
        name="Scene Name",
        description="Will become the parent folder under '<Project Directory>/Assets/' directory, where all files will be exported to. Example: '<Project Directory>/Assets/<Scene Name>/'.",
        maxlen=256,
        default="",
        subtype=BpyPropertySubtype.BYTE_STRING,
    )
    projectDir: bpy.props.StringProperty(
        name="Project Directory",
        description="Required. Root folder of the game/project.",
        maxlen=1024,
        default="",
        subtype=BpyPropertySubtype.DIR_PATH,
        set=ProjectDirSet,
        get=ProjectDirGet,
    )
    progressBar: bpy.props.IntProperty(
        subtype=BpyPropertySubtype.PERCENTAGE, min=0, max=100
    )
    mostRecentExportLog: bpy.props.StringProperty(
        name="Export Log",
        description="Name of the most recent export log.",
        default="",
        subtype=BpyPropertySubtype.BYTE_STRING,
    )


###############################################################################
# Operators
###############################################################################
class ModalExportSceneOperator(bpy.types.Operator):
    """
    Button/Operator for exporting the scene.
    """

    bl_idname = "o3dexport.exportscene"
    bl_label = "Export Scene"
    bl_description = "Exports the whole scene or the selected objects in an O3DE-ready SceneGraph JSON format, along with Meshes, Materials and Textures."
    # Custom properties
    _timer = None
    _expectedWorkCount = 0
    _progressWorkCount = 0
    _progressUpdated = False
    _exportIterator = None
    _exportCtx = None
    sceneName: str
    exportDir: str
    objectToExport: bpy.types.Object
    logfilePath: str = ""
    logfileObj: TextIO = None
    exportSelected: bool = False

    def modal(self, context, event):
        context.area.tag_redraw()
        if event.type in {"ESC"}:
            self.finish(context)
            return {"CANCELLED"}
        try:
            msg = next(self._exportIterator)
            self.report({"INFO"}, msg)
            self._progressWorkCount += 1
        except StopIteration:
            self.finish(context)
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR_INVALID_INPUT"}, "Error: " + str(e))
            self.finish(context)
            return {"CANCELLED"}
        progress = self._progressWorkCount / self._expectedWorkCount
        myprops = context.scene.o3mat
        myprops.progressBar = int(progress * 100)
        return {"PASS_THROUGH"}

    def CloseStdout(self):
        if self.logfileObj is None:
            return
        sys.stdout = sys.__stdout__
        self.logfileObj.close()
        self.logfileObj = None

    def cancel(self, context):
        self.CloseStdout()

    def finish(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        finalMsg = f"[{current_time}] Asset '[{self._progressWorkCount}/{self._expectedWorkCount}]' exported successfully"
        self.report({"INFO"}, finalMsg)
        _ShowMessageBox(finalMsg)
        myprops = context.scene.o3mat
        myprops.progressBar = 0
        self.CloseStdout()

    def execute(self, context):
        myprops = context.scene.o3mat
        self._exportCtx = export_settings.ExportSettings(
            self.exportDir,
            self.sceneName,
            myprops.forwardAxisOption,
            myprops.upAxisOption,
            myprops.overwriteTextures,
            myprops.overwriteMaterials,
            myprops.overwriteMeshes,
            myprops.overwriteSceneGraph,
            myprops.materialsNormalFlipXChannel,
            myprops.materialsNormalFlipYChannel,
        )
        sceneGraph = scenegraph.SceneGraph(
            self.objectsToExport, recursive=(not self.exportSelected)
        )
        textureCount = sceneGraph.CalculateTextureCount()
        materialCount = len(sceneGraph.GetMaterialsDictionary())
        meshCount = len(sceneGraph.GetMeshesDictionary())
        self._expectedWorkCount = textureCount + materialCount + meshCount
        # Add one more count if the SceneGraph will be generated.
        self._expectedWorkCount += 1 if sceneGraph.IsRecursive() else 0
        # + len(objectAndMaterialsList)
        self._progressWorkCount = 0
        myprops.progressBar = 0
        self._exportIterator = exporter.ExportAssetsAndSceneGraph(
            self._exportCtx, sceneGraph
        )

        if self._expectedWorkCount < 1:
            _ShowMessageBox("There's nothing to export in this scene!")
            return {"FINISHED"}

        # Define the Timer
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        return {"RUNNING_MODAL"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        exportSelected = len(context.selected_objects) > 0
        # If the scene name has not been defined, then auto populate the scene
        # name from the blend file name
        myprops = context.scene.o3mat
        sceneName = myprops.sceneName.decode("utf-8")
        if len(sceneName) < 1:
            sceneName = fileutils.GetBlendFilenameStem()
            myprops.sceneName = sceneName.encode()
        self.logfilePath = fileutils.GetExportLogFilepath(sceneName)
        try:
            self.logfileObj = open(self.logfilePath, "wt")
            sys.stdout = self.logfileObj
        except Exception as e:
            self.report(
                {"ERROR"},
                f"Won't be able to redirect stdout to '{self.logfilePath}':\n{e}",
            )
        myprops.mostRecentExportLog = os.path.basename(self.logfilePath).encode("utf-8")
        # It is very important to call this function so the data_blocks of all the objects
        # we may export get loaded into memory. Otherwise we'd have to click on every object
        # manually to get their data blocks like Transforms available.
        bpy.context.view_layer.update()
        if not exporter.AreImageDataBlocksAvailable():
            if context.space_data.shading.type != "MATERIAL":
                context.space_data.shading.type = (
                    "MATERIAL"  # Force texture load in the data blocks
                )
                msg = "Images are not ready to export. Try again in a few seconds."
                self.report({"ERROR"}, msg)
                _ShowMessageBox(msg)
                return {"CANCELLED"}
            elif not myprops.allowInvalidTextures:
                msg = "There are invalid textures in the scene. Can not proceed because invalid textures are not allowed."
                self.report({"ERROR"}, msg)
                _ShowMessageBox(msg)
                return {"CANCELLED"}
        if exportSelected:
            objectsToExport = context.selected_objects
        else:
            objectsToExport = exporter.GetOrphanObjects(context)
        if len(objectsToExport) < 1:
            self.report(
                {"ERROR_INVALID_INPUT"},
                "Error: There are no objects to export",
            )
            return {"CANCELLED"}
        exportDir = myprops.projectDir
        exportDir = "" if (exportDir is None) else exportDir.strip()
        if not exportDir:
            self.report({"ERROR"}, "Error: An output directory is necessary")
            return {"CANCELLED"}
        if not fileutils.IsO3DEProjectOrGemDir(exportDir):
            msg = f"Output directory '{exportDir}' needs to be an O3DE Root Project or Root Gem folder"
            self.report({"ERROR"}, msg)
            _ShowMessageBox(msg)
            return {"CANCELLED"}
        self.exportDir = exportDir
        self.sceneName = sceneName
        self.objectsToExport = objectsToExport
        self.exportSelected = exportSelected
        return self.execute(context)


###############################################################################
# UI
###############################################################################
class O3DEXPORT_VIEW_3D_PT_scene_export(bpy.types.Panel):
    """
    This panel class presents the options to export the scene or selected
    objects to O3DE-ready textures, materials, meshes and scene graph.
    """

    bl_label = "Scene Export options"
    bl_idname = "O3DEXPORT_VIEW_3D_PT_fbx_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "O3DEXPORT"
    bl_order = 100  # Make sure this is always the bottom most panel.

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.prop(scene.o3mat, "overwriteTextures")

        # Material options
        row = layout.row()
        materialBox = row.box()
        materialBox.label(text="Global Material Options")
        row = materialBox.row()
        row.prop(scene.o3mat, "overwriteMaterials")
        normalBox = materialBox.box()
        normalBox.label(text="Normal")
        row = normalBox.row()
        row.prop(scene.o3mat, "materialsNormalFlipXChannel")
        row = normalBox.row()
        row.prop(scene.o3mat, "materialsNormalFlipYChannel")

        row = layout.row()
        row.prop(scene.o3mat, "overwriteMeshes")
        row = layout.row()
        row.prop(scene.o3mat, "overwriteSceneGraph")

        row = layout.row()
        col = row.column(align=True)
        col.prop(scene.o3mat, "forwardAxisOption")
        col = row.column(align=True)
        col.prop(scene.o3mat, "upAxisOption")

        row = layout.row()
        row.prop(scene.o3mat, "allowInvalidTextures")
        row = layout.row()
        row.prop(scene.o3mat, "sceneName")
        row = layout.row()
        row.prop(scene.o3mat, "projectDir")

        row = layout.row()
        if len(context.selected_objects) > 0:
            row.operator("o3dexport.exportscene", text="Export Selected Object(s)")
        else:
            row.operator("o3dexport.exportscene")

        row = layout.row()
        row.prop(scene.o3mat, "progressBar")

        row = layout.row()
        row.prop(scene.o3mat, "mostRecentExportLog")


###############################################################################
# Registration
###############################################################################
classes = (
    O3matPropertyGroup,
    ModalExportSceneOperator,
    O3DEXPORT_VIEW_3D_PT_scene_export,
)


def register():
    for class_ in classes:
        bpy.utils.register_class(class_)
    bpy.types.Scene.o3mat = bpy.props.PointerProperty(type=O3matPropertyGroup)


def unregister():
    for class_ in classes:
        bpy.utils.unregister_class(class_)
    del bpy.types.Scene.o3mat


def _myDebugMain():
    """
    Used for debugging purposes, when it is not convenient to register the UI
    of this plugin.
    """
    print("\n\n\n\nWelcome To _myDebugMain\n")


if __name__ == "__main__":
    register()
    # Comment when not debugging
    # _myDebugMain()
