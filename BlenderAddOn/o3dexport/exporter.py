"""
Copyright (c) Contributors to the Open 3D Engine Project.
For complete copyright and license terms please see the LICENSE at the root of this distribution.

SPDX-License-Identifier: Apache-2.0 OR MIT
"""

# Created by Galib Arrieta (aka galibzon@github, lumbermixalot@github)
# under contract with Meta Platforms, Inc.
# Donated by Meta Platforms, Inc as an open source project.

import os
from collections.abc import Iterator

import bpy

# o3dexport modules
if __package__ is None or __package__ == "":
    import export_settings
    import mesh_exporter

    # When running as a standalone script from Blender Text View "Run Script"
    import o3material
    import scenegraph
    import texture_exporter
    import textureasset
else:
    # When running as an installed AddOn, then it runs in package mode.
    from . import (
        export_settings,
        mesh_exporter,
        o3material,
        scenegraph,
        texture_exporter,
        textureasset,
    )


def _ExportMaterial(
    exportSettings: export_settings.ExportSettings,
    material: o3material.O3Material,
    texturesDict: dict[str, textureasset.TextureAsset],
):
    """
    @param texturesDict A Dictionary that contains all TextureAssets in the scene, organized by texture name.
    """
    overwriteMaterials = exportSettings.GetFlagOverwriteMaterials()
    materialPath = exportSettings.GetO3DEMaterialExportPath(material)
    flipXChannel, flipYChannel = exportSettings.GetMaterialNormalFlipChannelOptions()
    if overwriteMaterials or (not os.path.exists(materialPath)):
        material.texturesDictionary = texturesDict
        if not o3material.SaveAsO3DEMaterial(
            material,
            materialPath,
            exportSettings.GetTextureAssetsDirectory(assetRootRelative=True),
            flipXChannel,
            flipYChannel,
        ):
            raise Exception(f"Failed to save O3DE material as '{materialPath}'")
        print(f"Created material file '{materialPath}'")
    else:
        print(f"Skipped material file '{materialPath}'")


def _ExportSceneGraph(
    exportSettings: export_settings.ExportSettings, sceneGraph: scenegraph.SceneGraph
) -> str:
    overwriteSceneGraph = exportSettings.GetFlagOverwriteSceneGraph()
    outputFilePath = exportSettings.GetSceneGraphExportPath()
    if os.path.exists(outputFilePath) and (not overwriteSceneGraph):
        print(f"SceneGraph '{outputFilePath}' already exists.")
        return outputFilePath
    if sceneGraph.SaveToFile(exportSettings.GetSceneName(), outputFilePath):
        return outputFilePath
    return ""


def ExportAssetsAndSceneGraph(
    exportSettings: export_settings.ExportSettings, sceneGraph: scenegraph.SceneGraph
) -> Iterator[str]:
    """
    Generator function that yields a message for each exported asset.
    Exports all assets in the scene according to the ExportSettings.
    In order to avoid blocking the UI when a scene is being exported, this function was made
    as a Generator, and the caller can choose to update the UI each time this function
    yields.
    """
    if not exportSettings.CreateOutputDirs():
        raise Exception("Failed to create output directories")
    print("O3DEXPORT: Created output directories")
    # First let's export the textures
    for _, textureAsset in sceneGraph.GetTexturesDictionary().items():
        for itor in texture_exporter.ExportTextureAsset(exportSettings, textureAsset):
            yield itor
    # Next, export the materials
    for materialName, material in sceneGraph.GetMaterialsDictionary().items():
        _ExportMaterial(exportSettings, material, sceneGraph.GetTexturesDictionary())
        yield f"O3DEXPORT: Exported Material '{materialName}'"

    # Next, export the meshes
    for meshName, meshAsset in sceneGraph.GetMeshesDictionary().items():
        obj = meshAsset.GetOwnerObject()
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        mesh_exporter.ExportMeshAsFbx(exportSettings, meshAsset.GetSanitizedName(), obj)
        obj.select_set(False)
        yield f"O3DEXPORT: Exported mesh '{meshName}' with sanitized name '{meshAsset.GetSanitizedName()}' from object '{obj.name}'"
    # Finally, create the SceneGraph only if the whole scene is being exported.
    if not sceneGraph.IsRecursive():
        msg = "O3DEXPORT: Completed exporting all assets only."
        print(msg)
        return msg  # noqa
    sceneFilePath = _ExportSceneGraph(exportSettings, sceneGraph)
    if sceneFilePath:
        msg = f"O3DEXPORT: Exported SceneGraph as '{sceneFilePath}'"
        print(msg)
        yield msg
    print("O3DEXPORT: Completed exporting all assets and objects!")


def AreImageDataBlocksAvailable():
    """
    @returns True if all images are loaded in memory and ready to be exported.
    """
    for image in bpy.data.images:
        if image.type != "IMAGE":
            continue
        if (image.users > 0) and (not image.has_data):
            return False
    return True


def GetOrphanObjects(context: bpy.types.Context) -> list[bpy.types.Object]:
    """
    Returns the list of only orphan Objects in the scene (Objects without Parent).
    """
    retList = []
    for obj in context.scene.objects:
        if obj.parent:
            continue
        retList.append(obj)
    return retList
