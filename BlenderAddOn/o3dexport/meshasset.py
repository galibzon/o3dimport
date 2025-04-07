"""
Copyright (c) Contributors to the Open 3D Engine Project.
For complete copyright and license terms please see the LICENSE at the root of this distribution.

SPDX-License-Identifier: Apache-2.0 OR MIT
"""

# Created by Galib Arrieta (aka galibzon@github, lumbermixalot@github)
# under contract with Meta Platforms, Inc.
# Donated by Meta Platforms, Inc as an open source project.

import bpy


def _SanitizeMeshName(meshName: str) -> str:
    """
    An FBX is exported with the name of the Mesh, and not the name of the owner
    object. The O3DE AssetProcessor is picky and doesn't like FBX filenames with
    the '.' character. We replace it here with "_".
    """
    sanitizedName = meshName.replace(".", "_")
    return sanitizedName


class MeshAsset:
    def __init__(self, name: str, ownerObject: bpy.types.Object):
        # Original mesh name as reported by Blender.
        self._name = name
        # Will be used as file name when exported as an O3DE asset.
        self._sanitizedName = _SanitizeMeshName(name)
        # Many objects can reference the same Mesh asset, we only need
        # one of the owners.
        self._ownerObject = ownerObject

    def GetName(self) -> str:
        return self._name

    def GetSanitizedName(self) -> str:
        return self._sanitizedName

    def GetOwnerObject(self) -> bpy.types.Object:
        return self._ownerObject
