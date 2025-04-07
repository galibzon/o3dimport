"""
Copyright (c) Contributors to the Open 3D Engine Project.
For complete copyright and license terms please see the LICENSE at the root of this distribution.

SPDX-License-Identifier: Apache-2.0 OR MIT
"""

# Created by Galib Arrieta (aka galibzon@github, lumbermixalot@github)
# under contract with Meta Platforms, Inc.
# Donated by Meta Platforms, Inc as an open source project.

import os

import bpy
import mathutils

# o3dexport modules
if __package__ is None or __package__ == "":
    # When running as a standalone script from Blender Text View "Run Script"
    import export_settings
else:
    # When running as an installed AddOn, then it runs in package mode.
    from . import export_settings


class TransformStore:
    """
    This class is used to store/restore an object's transform.
    We do three steps when exporting a Mesh:
    1. Store the object Transfrom.
    2- Set Transform to identity and export.
    3- Restore the original values of the object Transform.
    STEP:
    1. Save loc, rot, mode and scale.
    2. using bpy.ops Clear Parent.
    3. Set loc, rot, mode and scale to identity.
    4. using bpy.ops.object.parent_no_inverse_set(keep_transform=False) is
       equivalent as the menu option:
       Object -> Parent -> Make Parent Without Inverse.
       This causes the object to become a child of the parent "as-is", which at the
       moment the child (self._obj) has an Identity Transform.
       A typical parenting operation calculates inverse transforms to keep a child
       object at its original world location, BUT with its local transform recalculated
       as a child object. This is NOT what we need and that's why We call
       "Make Parent Without Inverse".
    5. Restore loc, rot, mode and scale.
    """

    def __init__(self, obj: bpy.types.Object):
        self._obj = obj
        self._parentObj = obj.parent
        self._prevLocation = obj.location.copy()
        self._prevScale = obj.scale.copy()
        self._prevRotationMode = obj.rotation_mode
        if self._prevRotationMode == "QUATERNION":
            self._prevQuaternion = obj.rotation_quaternion.copy()
        elif self._prevRotationMode == "AXIS_ANGLE":
            self._prevAxisAngle = obj.rotation_axis_angle
        else:
            self._prevEuler = obj.rotation_euler.copy()

    def ResetObjectTransform(self):
        # First unparent the object, otherwise
        # the object will appear in the FBX as parented to some transform.
        if self._parentObj:
            bpy.ops.object.parent_clear(type="CLEAR")
        self._obj.scale = (1, 1, 1)
        if self._prevRotationMode == "QUATERNION":
            self._obj.rotation_quaternion = mathutils.Quaternion()
        elif self._prevRotationMode == "AXIS_ANGLE":
            self._obj.rotation_axis_angle = (0.0, 0.0, 1.0, 0.0)
        else:
            self._obj.rotation_euler = (0.0, 0.0, 0.0)
        self._obj.location = (0, 0, 0)

    def RestoreObjectTransform(self):
        if self._parentObj:
            bpy.context.view_layer.objects.active = self._parentObj
            bpy.ops.object.parent_no_inverse_set(keep_transform=False)
        self._obj.location = self._prevLocation
        self._obj.rotation_mode = self._prevRotationMode
        if self._prevRotationMode == "QUATERNION":
            self._obj.rotation_quaternion = self._prevQuaternion
        elif self._prevRotationMode == "AXIS_ANGLE":
            self._obj.rotation_axis_angle = self._prevAxisAngle
        else:
            self._obj.rotation_euler = self._prevEuler
        self._obj.scale = self._prevScale


def ExportMeshAsFbx(
    exportSettings: export_settings.ExportSettings, meshName: str, obj: bpy.types.Object
):
    """
    Exports the currently selected object as an FBX file, where the Object Transform is exported
    as the identity.
    The function assumes that @obj is the selected object.
    """
    overwriteFBXs = exportSettings.GetFlagOverwriteFBXs()
    outputFilePath = exportSettings.GetMeshFbxExportPath(meshName)
    if os.path.exists(outputFilePath) and (not overwriteFBXs):
        print(f"FBX file '{outputFilePath}' already exists.")
        return
    tmResetter = TransformStore(obj)
    tmResetter.ResetObjectTransform()
    f, u = exportSettings.GetAxisOptions()
    bpy.ops.export_scene.fbx(
        filepath=outputFilePath,
        check_existing=False,
        use_selection=True,
        axis_forward=f,
        axis_up=u,
        path_mode="STRIP",
    )
    tmResetter.RestoreObjectTransform()
    print(f"Exported Mesh '{meshName}' from Obj '{obj.name}' as '{outputFilePath}'")
