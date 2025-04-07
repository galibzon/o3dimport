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
import OpenImageIO as oiio

# o3dexport modules
if __package__ is None or __package__ == "":
    import export_settings

    # When running as a standalone script from Blender Text View "Run Script"
    import fileutils
    import imageutils
    import textureasset
else:
    # When running as an installed AddOn, then it runs in package mode.
    from . import export_settings, fileutils, imageutils, textureasset


def _CreateResampledTexture(
    originalImageAsImageBuf: oiio.ImageBuf, colorChannel: str, resampledFinalOutputPath: str
):
    """
    Creates a one color channel texture file, from a numpy array.
    """
    colorChannelIds = {"Red": 0, "Green": 1, "Blue": 2, "Alpha": 3}
    colorChhanelId = colorChannelIds[colorChannel]
    newImage = imageutils.CreateImageBufFromColorChannel(
        originalImageAsImageBuf, colorChhanelId
    )
    newImage.write(resampledFinalOutputPath)
    print(f"Created '{resampledFinalOutputPath}'")


def _CreateResampledTextures(
    exportSettings: export_settings.ExportSettings,
    sanitizedTextureName: str,
    colorChannels: set[str],
) -> Iterator[str]:
    """
    Assumes the texture identified by @textureName was already exported.
    Creates a set of new, one channel, textures in disk where the specified
    color channels are extracted into each one of them.
    """
    originalSanitizedTextureName = sanitizedTextureName
    originalfinalOutputPath = os.path.join(
        exportSettings.GetTextureAssetsDirectory(), originalSanitizedTextureName
    )
    if not os.path.exists(originalfinalOutputPath):
        msg = f"ERROR: Was expecting the texture '{originalfinalOutputPath}' to exist!"
        print(msg)
        raise Exception(msg)
    overwriteTextures = exportSettings.GetFlagOverwriteTextures()
    for colorChannel in colorChannels:
        resampledFinalOutputName = fileutils.GetResampledSanitizedFilenameExtension(
            sanitizedTextureName, colorChannel
        )
        resampledFinalOutputPath = os.path.join(
            exportSettings.GetTextureAssetsDirectory(), resampledFinalOutputName
        )
        if (not overwriteTextures) and os.path.exists(resampledFinalOutputPath):
            msg = f"Skipped creating '{resampledFinalOutputPath}' from '{originalfinalOutputPath}' because texture overwrite is disabled."
        else:
            originalImageAsImageBuf = imageutils.LoadImageFileAsImageBuf(
                originalfinalOutputPath
            )
            _CreateResampledTexture(
                originalImageAsImageBuf, colorChannel, resampledFinalOutputPath
            )
            msg = (
                f"Created '{resampledFinalOutputPath}' from '{originalfinalOutputPath}'"
            )
        print(msg)
        yield msg


def ExportTextureAsset(
    exportSettings: export_settings.ExportSettings,
    textureAsset: textureasset.TextureAsset,
) -> Iterator[str]:
    """
    Typically only one Texture file is exported for each  TextureAsset object,
    but some textures are sampled on a given color channel. Given that the O3DE Material
    system doesn't support per channel sampling, our workaround is to generate
    one Texture file for each color channel that is sampled.

    This Generator function can produce up to five Texture files:
        [0] would be the original Textures will all of its channels (RGBA).
        [1] Red Channel Texture (Optional).
        [2] Green Channel Texture (Optional).
        [3] Blue Channel Texture (Optional).
        [4] Alpha Channel Texture (Optional).
    """
    originalTextureName = textureAsset.GetName()
    if originalTextureName not in bpy.data.images:
        msg = f"Texture named '{originalTextureName}' not found in bpy.data.images"
        print(msg)
        raise Exception(msg)
    image = bpy.data.images[originalTextureName]
    if not image.has_data:
        msg = f"Texture named '{originalTextureName}' has no data. Skipping."
        print(msg)
        return msg  # noqa
    finalOutputPath = os.path.join(
        exportSettings.GetTextureAssetsDirectory(), textureAsset.GetSanitizedName()
    )
    overwriteTextures = exportSettings.GetFlagOverwriteTextures()
    if overwriteTextures or (not os.path.exists(finalOutputPath)):
        try:
            image.save(filepath=finalOutputPath)
        except Exception as e:
            msg = f"Got exception when calling image.save('{finalOutputPath}'): {e}"
            print(msg)
            raise Exception(msg)
        msg = f"Exported texture '{originalTextureName}' As: {finalOutputPath}"
        print(msg)
    else:
        msg = f"Skipped exporting texture '{originalTextureName}' As: {finalOutputPath} because texture overwrite is disabled."
        print(msg)
    yield msg
    # If there are NO color channels to be sampled from the texture then We are done.
    if textureAsset.HasSampledChannels():
        # Each sampled color channel must be created as a texture.
        for itor in _CreateResampledTextures(
            exportSettings,
            textureAsset.GetSanitizedName(),
            textureAsset.GetSampledChannels(),
        ):
            yield itor
