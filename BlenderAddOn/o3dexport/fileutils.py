"""
Copyright (c) Contributors to the Open 3D Engine Project.
For complete copyright and license terms please see the LICENSE at the root of this distribution.

SPDX-License-Identifier: Apache-2.0 OR MIT
"""

# Created by Galib Arrieta (aka galibzon@github, lumbermixalot@github)
# under contract with Meta Platforms, Inc.
# Donated by Meta Platforms, Inc as an open source project.

import os
import pathlib
import time

import bpy

O3DE_ASSETS_FOLDER_NAME = "Assets"

# From : https://docs.blender.org/api/current/bpy_types_enum_items/image_type_items.html#rna-enum-image-type-items
SUPPORTED_BLENDER_IMAGE_TYPES = {
    "BMP": ".bmp",
    "PNG": ".png",
    "JPEG": ".jpeg",
}
SUPPORTED_IMAGE_FILE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp"}


def GetBlendFilenameStem() -> str:
    filename = bpy.path.basename(bpy.data.filepath)
    return pathlib.Path(filename).stem


def CreateDirectory(dirPath: str) -> bool:
    """
    Returns true if the directory already exists and is, in fact, a path to a directory.
    Returns false if the directory doesn't exist and it failed to create it.
    """
    if os.path.exists(dirPath) and os.path.isdir(dirPath):
        return True
    try:
        os.makedirs(dirPath)
        print(f"Created new directory '{dirPath}'")
        return True
    except Exception as e:
        print(f"Failed to create directory '{dirPath}', reason:\n{e}")
        return False


def IsO3DEProjectOrGemDir(dirPath: str) -> bool:
    projectJson = os.path.join(dirPath, "project.json")
    if os.path.exists(projectJson):
        return True
    gemJson = os.path.join(dirPath, "gem.json")
    if os.path.exists(gemJson):
        return True
    return False


def GetRelativePathAfterDir(
    dirPath: str, afterComponent: str = O3DE_ASSETS_FOLDER_NAME
) -> str:
    """
    If dirPath == "C:\\p1\\p2\\<afterComponent>\\p2\\p3
    returns "p2\\p3"
    """
    discoveredComponents = []
    allComponents = dirPath.split(os.path.sep)
    foundAfterComponent = False
    while len(allComponents):
        lastComponent = allComponents[-1]
        if lastComponent == "":
            allComponents = allComponents[:-1]
            continue
        if lastComponent == afterComponent:
            foundAfterComponent = True
            break  # Exit the while loop
        discoveredComponents.insert(0, lastComponent)
    if not foundAfterComponent:
        print(
            f"O3DETOPIA: dirPath '{dirPath}' does not contain the component '{afterComponent}'"
        )
        return ""
    return os.path.sep.join(discoveredComponents)


def SanitizeFilenameExtension(filename: str) -> str:
    """
    @param filename A filename that needs to be sanitized
    @returns @filename if it ends in a valid extension, otherwise returns
             a new string with a proper file extensin
    @exammples
        1- if @filename == "default_material.png" returns @filename
        2- if @filename == "default_material.png.003" returns "default_material.003.png"
    """
    _, ext = os.path.splitext(filename)
    if ext in SUPPORTED_IMAGE_FILE_EXTENSIONS:
        return filename
    tmpFilename = filename
    foundExt = ""
    for supportedExt in SUPPORTED_IMAGE_FILE_EXTENSIONS:
        tmpExt = f"{supportedExt}."
        if tmpExt in tmpFilename:
            tmpFilename = tmpFilename.replace(tmpExt, "")
            foundExt = supportedExt
            break
    if foundExt != "":
        return f"{tmpFilename}{foundExt}"
    return filename


def GetResampledSanitizedFilenameExtension(
    sanitizedTextureName: str, colorChannel: str
) -> str:
    sanitizedRoot, ext = os.path.splitext(sanitizedTextureName)
    return f"{sanitizedRoot}_{colorChannel}{ext}"


def GetAbsolutePathFromBlenderPath(blenderPath: str) -> str:
    """
    Transforms a Blender produced path like:
        "//../../../../../../P4W/O3deProjects/LightWrapDemo"
    into:
        "C:/P4W/O3deProjects/LightWrapDemo"
    """
    blenderAbsolute = bpy.path.abspath(blenderPath)
    osAbsolute = os.path.abspath(blenderAbsolute)
    return osAbsolute


def GetExportLogFilepath(sceneName: str) -> str:
    filename = bpy.data.filepath
    folder = os.path.split(filename)[0]
    local_time = time.localtime()
    formatted_time = time.strftime("%Y-%m-%d_%H-%M-%S", local_time)
    return os.path.join(folder, f"{sceneName}_{formatted_time}.log")
