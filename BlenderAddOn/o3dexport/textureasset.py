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
    # if ext:
    #    raise Exception(
    #        f"Texture name '{sanitizedTextureName}' has unsupported extension '{ext}'"
    #    )
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


class TextureAsset:
    def __init__(self, name: str):
        # Original texture name as reported by Blender.
        self._name = name
        # The santized name will be used as filename when it gets exported
        # as an O3DE asset.
        self._sanitizedName = _SanitizeTextureName(name)
        # Typically empty, but for the few cases when a material
        # samples one or more color channels, the name of the color
        # channels are added here.
        self._sampledChannels = set()

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
