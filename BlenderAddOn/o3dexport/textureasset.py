"""
Copyright (c) Contributors to the Open 3D Engine Project.
For complete copyright and license terms please see the LICENSE at the root of this distribution.

SPDX-License-Identifier: Apache-2.0 OR MIT
"""

# Created by Galib Arrieta (aka galibzon@github, lumbermixalot@github)
# under contract with Meta Platforms, Inc.
# Donated by Meta Platforms, Inc as an open source project.

import os
import re

import bpy

# o3dexport modules
if __package__ is None or __package__ == "":
    # When running as a standalone script from Blender Text View "Run Script"
    import fileutils
else:
    # When running as an installed AddOn, then it runs in package mode.
    from . import fileutils


def _SanitizeTextureName(textureName: str) -> str:
    """
    A proper texture name would be "<name>.<ext>", for example:
    "wall.png" or "floor.jpg". In these simple cases this function
    returns @textureName.
    But, sometimes there are cases like these:
    "wall.png.001": In this case the sanitized name should be "wall.001.png".
    Another case is when the texture has no apparent extension like "wall",
    in such case we need to dig into bpy.data and find the Image Type and based
    on the Image Type the sanitized name is returned as "wall.png"
    """
    sanitizedTextureName = fileutils.SanitizeFilenameExtension(textureName)
    # Verify that the file has an extension, if not, we'll add an extension based
    # on the data from bpy.data.images.
    _, ext = os.path.splitext(sanitizedTextureName)
    if ext in fileutils.SUPPORTED_IMAGE_FILE_EXTENSIONS:
        return sanitizedTextureName
    # Discover the extension using bpy.data.images.
    image = bpy.data.images[textureName]
    if not image.has_data:
        print(f"WARNING: Image with texture name '{textureName}' has no data!")
        return sanitizedTextureName
    if image.file_format not in fileutils.SUPPORTED_BLENDER_IMAGE_TYPES:
        raise Exception(
            f"Image with texture name '{textureName}' has unsupported file format '{image.file_format}'"
        )
    sanitizedTextureName = f"{sanitizedTextureName}{fileutils.SUPPORTED_BLENDER_IMAGE_TYPES[image.file_format]}"
    return sanitizedTextureName


def _SanitizeTexturNameForNormalMap(textureFilename: str) -> str:
    """
    @param textureName From O3DE:
           AZStd::string BuilderSettingManager::GetFileMask(AZStd::string_view imageFilePath) const
           If the complete file name contains multiple extension separators ('.'), only use the base name before the first separator
           for the file mask. For example, 'name_filemask.something.extension' will only use 'name_filemask', producing a result
           of '_filemask' that is returned from this method.
    """
    arr = textureFilename.split('.', 1)
    basename = arr[0]
    ext = None
    if len(arr) > 1:
        ext = arr[1]
    arr = basename.rsplit('_', 1)
    if len(arr) == 1:
        #There's no "_something". Add "_normal".
        basename += "_normal"
        if ext:
            basename += f".{ext}"
        return basename
    basename = arr[0]
    suffix = arr[1]
    suffix = suffix.lower()
    if suffix == 'normal':
        # All good. return the same textureFilename
        return textureFilename
    #If we are here we need to add _normal.
    newFilename = f"{basename}_{suffix}_normal"
    if ext:
        newFilename += f".{ext}"
    return newFilename


def _UpdateTextureNameVersion(textureName: str) -> str:
    """
    textureName can be:
        - 'Image.png' -> Return 'Image001.png'
        - 'Image001.png' -> Return 'Image002.png'
        - 'Image003.png' -> Return 'Image004.png'
        - 'Image_normal.jpg' -> Return 'Image001_normal.jpg'
    """
    arr = textureName.split('.', 1)
    basename = arr[0]
    ext = None
    if len(arr) > 1:
        ext = arr[1]
    arr =  basename.split('_', 1)
    baseLeft = arr[0]
    baseRight = None
    if len(arr) > 1:
        baseRight = arr[1]
    matchObj = re.search(r'\D+(\d+)$', baseLeft)
    if matchObj is None:
        newname = f"{baseLeft}111"
        if baseRight:
            newname += f"_{baseRight}"
        if ext:
            newname += f".{ext}"
        return newname
    digitsStr = matchObj.group(1)
    asNumber = int(digitsStr)
    asNumber += 1
    newNumberStr = f"{asNumber:03}"
    newname = baseLeft.replace(digitsStr, newNumberStr)
    if baseRight:
        newname += f"_{baseRight}"
    if ext:
        newname += f".{ext}"
    return newname


class TextureAsset:
    # This static variable is used to guarantee uniqueness of sanitized texture names.
    # For example In Blender, we have found distinct texture assets named "Image" and "Image.png"
    # Both cases would produce the same sanitized texture file name:
    # "Image" -> "Image.png"
    # "Image.png" -> "Image.png"
    # To avoid this problem, we will keep this set where we can check if a sanitized texture name is unique.
    _uniqueSanitizedNames = set()
    def __init__(self, name: str):
        # Original texture name as reported by Blender.
        self._name = name
        # The santized name will be used as filename when it gets exported
        # as an O3DE asset.
        self._sanitizedName = self._GetUniqueSanitizedTextureName(name)
        # Typically empty, but for the few cases when a material
        # samples one or more color channels, the name of the color
        # channels are added here.
        self._sampledChannels = set()
        self._isNormalMap = False

    def _GetUniqueSanitizedTextureName(self, name) -> str:
        sanitizedName = _SanitizeTextureName(name)
        while sanitizedName in TextureAsset._uniqueSanitizedNames:
            sanitizedName = _UpdateTextureNameVersion(sanitizedName)
        TextureAsset._uniqueSanitizedNames.add(sanitizedName)
        return sanitizedName

    def GetName(self) -> str:
        return self._name

    def GetSanitizedName(self) -> str:
        return self._sanitizedName

    def GetSampledChannels(self) -> set[str]:
        return self._sampledChannels

    def HasSampledChannels(self) -> bool:
        return len(self._sampledChannels) > 0

    def UpdateSampledChannels(self, rhs):
        newSet = self._sampledChannels | rhs._sampledChannels
        self._sampledChannels = newSet

    def SanitizeNameAsNormalMap(self):
        """
        This function is called by o3material as soon as it knows
        this texture will be used as a normal map. Its sanitized
        name should contain XXX_normal.XXX so the O3DE Asset Processor
        knows that the RGB data is a Tangent Space normal map instead of
        a color image. 
        """
        self._sanitizedName = _SanitizeTexturNameForNormalMap(self._sanitizedName)
        self._isNormalMap = True


    def IsNormalMap(self):
        return self._isNormalMap