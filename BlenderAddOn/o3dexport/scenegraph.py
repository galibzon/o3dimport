"""
Copyright (c) Contributors to the Open 3D Engine Project.
For complete copyright and license terms please see the LICENSE at the root of this distribution.

SPDX-License-Identifier: Apache-2.0 OR MIT
"""

# Created by Galib Arrieta (aka galibzon@github, lumbermixalot@github)
# under contract with Meta Platforms, Inc.
# Donated by Meta Platforms, Inc as an open source project.

import copy
import json
import math

import bpy
import mathutils

# o3dexport modules
if __package__ is None or __package__ == "":
    import meshasset

    # When running as a standalone script from Blender Text View "Run Script"
    import o3material
    import textureasset
else:
    # When running as an installed AddOn, then it runs in package mode.
    from . import meshasset, o3material, textureasset


# The following class works as namespace for some Blender String Constants that
# trigger Flake-type errors during Static Analysis.
# https://docs.blender.org/api/current/bpy_types_enum_items/object_type_items.html#rna-enum-object-type-items\
class ObjType:
    MESH = "MESH"
    EMPTY = "EMPTY"

    def __init__(self):
        pass


class RotationModes:
    QUATERNION = "QUATERNION"
    AXIS_ANGLE = "AXIS_ANGLE"
    XYZ = "XYZ"

    def __init__(self):
        pass


class SceneGraph:
    """
    From a list of Objects, discovers and organizes
    all the data that can be exported to O3DE.
    The major groups of assets that are discovered with this class:
    1. List of unique Meshes (each mesh exported as a single FBX).
    2. List of unique Textures
    3. List of unique Materials
    4. The scene hierarchy (exported as a JSON file).
    """

    def __init__(self, objects: list[bpy.types.Object], recursive: bool):
        # Original flat list of all the objects to export.
        self._objects = objects
        self._recursive = recursive
        # A dictionary of all the Meshes organized by Mesh Name
        #     key: Mesh name
        #     value: MeshAsset object (Remark: A single Mesh may be referenced by several Objects).
        self._meshesByMeshName = {}
        # A dictionary of all the Materials, organized by Material name.
        #     key: Material name.
        #     value: The material as class o3material.O3Material
        self._materialsByMaterialName = {}
        # A dictionary of all the materials, organized by Object name.
        #     key: Object name.
        #     value: list[o3material.O3Material].
        self._materialsByObjectName = {}
        # A dictionary of all the TextureAsset(s), organized by texture name.
        #     key: Original (unsanitized) Texture name
        #     value: textureasset.TextureAsset
        self._texturesByTextureName = {}
        self._DiscoverAssetsFromObjects(objects)

    def IsRecursive(self) -> bool:
        return self._recursive

    def GetTexturesDictionary(self) -> dict[str, textureasset.TextureAsset]:
        return self._texturesByTextureName

    def GetMaterialsDictionary(self) -> dict[str, o3material.O3Material]:
        return self._materialsByMaterialName

    def GetMeshesDictionary(self) -> dict[str, meshasset.MeshAsset]:
        return self._meshesByMeshName

    def CalculateTextureCount(self) -> int:
        """
        Returns the total count of textures that will be created/exported.
        """
        count = 0
        for _, textureAsset in self._texturesByTextureName.items():
            # The original texture is always exported
            # and, of course, each sampled channel will also become
            # a texture of a single color channel.
            count += 1 + len(textureAsset.GetSampledChannels())
        return count

    def SaveToFile(self, sceneName: str, outputFilePath: str) -> bool:
        sceneDictionary = self._BuildSceneDictionary(sceneName)
        jsonString = json.dumps(sceneDictionary, indent=4)
        try:
            with open(outputFilePath, "w") as file:
                file.write(jsonString)
        except Exception as e:
            print(
                f"Error trying to save scene '{sceneName}' at path '{outputFilePath}'. Error: {e}"
            )
            return False
        return True

    def _DiscoverAssetsFromObjects(self, objectList: list[bpy.types.Object]):
        """
        Discovers the Meshes, Textures and Materials referenced by all objects
        in @objectList
        """
        for obj in objectList:
            if obj.type != ObjType.MESH:
                if self._recursive:
                    self._DiscoverAssetsFromObjects(obj.children)
                continue
            meshName = obj.data.name
            self._meshesByMeshName[meshName] = meshasset.MeshAsset(meshName, obj)
            objMaterials = o3material.GetMaterialsFromObject(obj)
            for material in objMaterials:
                self._materialsByMaterialName[material.GetName()] = material
                textureList = material.BuildTextureList()
                self._UpdateTexturesDictionary(textureList, self._texturesByTextureName)
            self._materialsByObjectName[obj.name] = objMaterials
            if self._recursive:
                self._DiscoverAssetsFromObjects(obj.children)

    def _UpdateTexturesDictionary(
        self,
        textureListIn: list[textureasset.TextureAsset],
        texturesByTextureNameOut: dict[str, textureasset.TextureAsset],
    ):
        """
        Adds textures from @textureListIn into @texturesByTextureNameOut if not added previously.
        If the texture already exist in @texturesByTextureNameOut, then only the SampledChannels
        set is updated.
        """
        for textureAsset in textureListIn:
            if textureAsset.GetName() in texturesByTextureNameOut:
                prevTextureAsset = texturesByTextureNameOut[textureAsset.GetName()]
                prevTextureAsset.UpdateSampledChannels(textureAsset)
            else:
                texturesByTextureNameOut[textureAsset.GetName()] = copy.deepcopy(
                    textureAsset
                )

    def _BuildSceneDictionary(self, sceneName: str) -> dict:
        # This will be a recursive process starting from the root objects
        outputDict = {
            "name": sceneName,
            "children": self._BuildObjectListRecursive(self._objects),
        }
        return outputDict

    def _BuildObjectListRecursive(self, objectList: list[bpy.types.Object]) -> list:
        retList = []
        for obj in objectList:
            objDictionary = self._BuildObjectDictionary(obj)
            if len(obj.children) > 0:
                objDictionary["children"] = self._BuildObjectListRecursive(obj.children)
            retList.append(objDictionary)
        return retList

    def _BuildObjectDictionary(self, obj: bpy.types.Object) -> dict:
        retDict = {
            "name": obj.name,
            "transform": self._BuildLocalTransformDictionary(obj),
        }
        if obj.type == ObjType.MESH:
            if obj.data.name in self._meshesByMeshName:
                meshasset = self._meshesByMeshName[obj.data.name]
                retDict["mesh"] = meshasset.GetSanitizedName()
        if obj.name in self._materialsByObjectName:
            materialList = self._materialsByObjectName[obj.name]
            materialsNameList = []
            for material in materialList:
                materialsNameList.append(material.GetName())
            retDict["materials"] = materialsNameList
        return retDict

    def _BuildLocalTransformDictionary(self, obj: bpy.types.Object) -> dict:
        # Let's convert the object rotation to O3DE Eulers (degrees)
        if obj.rotation_mode == RotationModes.QUATERNION:
            rotationEulers = self._BuildRotationEulersFromQuaternion(
                obj.rotation_quaternion
            )
        elif obj.rotation_mode == RotationModes.AXIS_ANGLE:
            rotationEulers = self._BuildRotationEulersFromAxisAngle(
                obj.rotation_axis_angle
            )
        elif obj.rotation_mode == RotationModes.XYZ:
            rotationEulers = self._BuildRotationEulersFromXYZEulers(obj.rotation_euler)
        else:
            rotationEulers = [0.0, 0.0, 0.0]
            raise Exception(
                f"Object with name '{obj.name}' has unsupported rotation mode '{obj.rotation_mode}'"
            )
        retDict = {
            "translate": tuple(obj.location),
            "rotate": rotationEulers,
            "scale": tuple(obj.scale),
        }
        return retDict

    def _BuildRotationEulersFromXYZEulers(
        self, eulers: mathutils.Euler
    ) -> tuple[float, float, float]:
        degX = math.degrees(eulers.x)
        degY = math.degrees(eulers.y)
        degZ = math.degrees(eulers.z)
        return (degX, degY, degZ)

    def _BuildRotationEulersFromQuaternion(
        self, quat: mathutils.Quaternion
    ) -> tuple[float, float, float]:
        eulerRads = quat.to_euler("XYZ")
        return self._BuildRotationEulersFromXYZEulers(eulerRads)

    def _BuildRotationEulersFromAxisAngle(
        self, axisAngle: tuple[float, float, float, float]
    ) -> tuple[float, float, float]:
        axis = (axisAngle[0], axisAngle[1], axisAngle[2])
        quat = mathutils.Quaternion(axis, axisAngle[3])
        return self._BuildRotationEulersFromQuaternion(self, quat)
