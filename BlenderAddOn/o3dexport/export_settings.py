"""
Copyright (c) Contributors to the Open 3D Engine Project.
For complete copyright and license terms please see the LICENSE at the root of this distribution.

SPDX-License-Identifier: Apache-2.0 OR MIT
"""

# Created by Galib Arrieta (aka galibzon@github, lumbermixalot@github)
# under contract with Meta Platforms, Inc.
# Donated by Meta Platforms, Inc as an open source project.

import os

# o3dexport modules
if __package__ is None or __package__ == "":
    # When running as a standalone script from Blender Text View "Run Script"
    import fileutils
    import o3material
else:
    # When running as an installed AddOn, then it runs in package mode.
    from . import fileutils, o3material


class ExportSettings:
    """
    Works as a collection of flags and properties that describe what/how to export
    the scene.
    """

    def __init__(
        self,
        outputDir: str,
        sceneName: str,
        forwardAxisOption: str,
        upAxisOption: str,
        overwriteTextures: bool,
        overwriteMaterials: bool,
        overwriteFBXs: bool,
        overwriteSceneGraph: bool,
        materialsNormalFlipXChannel: bool,
        materialsNormalFlipYChannel: bool,
    ):
        """
        @param outputDir is typically the root of the game project
        @param forwardAxisOption Axis string name as required by bpy.ops.export_scene.fbx
               enum in ['X', 'Y', 'Z', '-X', '-Y', '-Z']
        @param upAxisOption: Axis string name as required by bpy.ops.export_scene.fbx
               enum in ['X', 'Y', 'Z', '-X', '-Y', '-Z']
        """
        self._sceneName = sceneName
        self._assetsRelativeSceneDir = os.path.join(
            fileutils.O3DE_ASSETS_FOLDER_NAME, "Scenes", sceneName
        )
        # Absolute path of the scene folder
        self._absoluteSceneDir = os.path.join(outputDir, self._assetsRelativeSceneDir)
        # Textures
        self._absoluteTexturesDir = os.path.join(self._absoluteSceneDir, "Textures")
        self._assetsRelativeTexturesDir = os.path.join(
            self._assetsRelativeSceneDir, "Textures"
        )
        # Materials
        self._absoluteMaterialsDir = os.path.join(self._absoluteSceneDir, "Materials")
        self._assetsRelativeMaterialsDir = os.path.join(
            self._assetsRelativeSceneDir, "Materials"
        )
        # Meshes
        self._absoluteMeshesDir = os.path.join(self._absoluteSceneDir, "Meshes")
        self._assetsRelativeMeshesDir = os.path.join(
            self._assetsRelativeSceneDir, "Meshes"
        )
        # Store the axis options
        self._forwardAxisOption = forwardAxisOption
        self._upAxisOption = upAxisOption
        # Store the flags.
        self._overwriteTextures = overwriteTextures
        self._overwriteMaterials = overwriteMaterials
        self._overwriteFBXs = overwriteFBXs
        self._overwriteSceneGraph = overwriteSceneGraph
        self._materialsNormalFlipXChannel = materialsNormalFlipXChannel
        self._materialsNormalFlipYChannel = materialsNormalFlipYChannel

    def CreateOutputDirs(self) -> bool:
        return (
            fileutils.CreateDirectory(self._absoluteSceneDir)
            and fileutils.CreateDirectory(self._absoluteTexturesDir)
            and fileutils.CreateDirectory(self._absoluteMaterialsDir)
            and fileutils.CreateDirectory(self._absoluteMeshesDir)
        )

    def GetSceneName(self) -> str:
        return self._sceneName

    def GetTextureAssetsDirectory(self, assetRootRelative: bool = False) -> str:
        """
        Returns the output directory, in the O3DE project, where Texture files will
        be exported to.
        Returns an absolute path, unless @assetRootRelative is True, which would return
        a path relative to the '<O3DE Project>/' folder.
        """
        return (
            self._assetsRelativeTexturesDir
            if assetRootRelative
            else self._absoluteTexturesDir
        )

    def GetMaterialAssetsDirectory(self, assetRootRelative: bool = False) -> str:
        """
        Returns the output directory, in the O3DE project, where Material files will
        be exported to.
        Returns an absolute path, unless @assetRootRelative is True, which would return
        a path relative to the '<O3DE Project>/' folder.
        """
        return (
            self._assetsRelativeMaterialsDir
            if assetRootRelative
            else self._absoluteMaterialsDir
        )

    def GetMeshAssetsDirectory(self, assetRootRelative: bool = False) -> str:
        """
        Returns the output directory, in the O3DE project, where Mesh assets (FBX) files will
        be exported to.
        Returns an absolute path, unless @assetRootRelative is True, which would return
        a path relative to the '<O3DE Project>/Assets/' folder.
        """
        return (
            self._assetsRelativeMeshesDir
            if assetRootRelative
            else self._absoluteMeshesDir
        )

    def GetSceneDirPath(self) -> str:
        return self._absoluteSceneDir

    def GetMeshFbxExportPath(
        self, meshName: str, assetRootRelative: bool = False
    ) -> str:
        outputFilePath = os.path.join(
            self.GetMeshAssetsDirectory(assetRootRelative), f"{meshName}.fbx"
        )
        return outputFilePath

    def GetO3DEMaterialExportPath(
        self, material: o3material.O3Material, assetRootRelative: bool = False
    ) -> str:
        outputFilePath = os.path.join(
            self.GetMaterialAssetsDirectory(assetRootRelative),
            f"{material.GetName()}.material",
        )
        return outputFilePath

    def GetSceneGraphExportPath(self) -> str:
        outputFilePath = os.path.join(self._absoluteSceneDir, f"{self._sceneName}.sgr")
        return outputFilePath

    def GetFowardAxisOption(self) -> str:
        return self._forwardAxisOption

    def GetUpAxisOption(self) -> str:
        return self._upAxisOption

    def GetAxisOptions(self) -> tuple[str, str]:
        return self._forwardAxisOption, self._upAxisOption

    def GetFlagOverwriteTextures(self) -> bool:
        return self._overwriteTextures

    def GetFlagOverwriteMaterials(self) -> bool:
        return self._overwriteMaterials

    def GetFlagOverwriteFBXs(self) -> bool:
        return self._overwriteFBXs

    def GetFlagOverwriteSceneGraph(self) -> bool:
        return self._overwriteSceneGraph

    def GetMaterialNormalFlipChannelOptions(self) -> tuple[bool, bool]:
        return self._materialsNormalFlipXChannel, self._materialsNormalFlipYChannel
