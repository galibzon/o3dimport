"""
Copyright (c) Contributors to the Open 3D Engine Project.
For complete copyright and license terms please see the LICENSE at the root of this distribution.

SPDX-License-Identifier: Apache-2.0 OR MIT
"""

# Created by Galib Arrieta (aka galibzon@github, lumbermixalot@github)
# under contract with Meta Platforms, Inc.
# Donated by Meta Platforms, Inc as an open source project.

import json
import os
import posixpath

import bpy
import mathutils

# o3dexport modules
if __package__ is None or __package__ == "":
    # When running as a standalone script from Blender Text View "Run Script"
    import fileutils
    import textureasset
else:
    # When running as an installed AddOn, then it runs in package mode.
    from . import fileutils, textureasset

# Should use unix/posix file separator
PROJECT_ROOT = "@projectroot@"


def _get_values_from_keys_with_name(dictionary: dict, key_name: str) -> list[str]:
    """
    Recursively search for keys with the given name in a dictionary.

    Args:
        dictionary (dict): The dictionary to search.
        key_name (str): The name of the key to search for.

    Returns:
        list: A list of values with the given name.
    """
    retValues = []
    for key, value in dictionary.items():
        if key == key_name and len(value) > 0:
            retValues.append(value)
        elif isinstance(value, dict):
            retValues.extend(_get_values_from_keys_with_name(value, key_name))
    return retValues


def DumpNodeInputs(indentation: str, node: bpy.types.Node):
    for idx, inputSocket in enumerate(node.inputs):
        print(
            f"{indentation}[{idx}]:{inputSocket.name}, Type:{inputSocket.type}, Value:{inputSocket.default_value}, IsLinked={inputSocket.is_linked}"
        )


def DumpNodeLink(indentation: str, nodeLink: bpy.types.NodeLink):
    if not nodeLink.is_valid:
        return
    print(
        f"{indentation}From:{nodeLink.from_node.name}, Socket:{nodeLink.from_socket.name}"
    )
    DumpNodeInputs(f"{indentation}  ", nodeLink.from_node)


class O3Material:
    """
    The O3DEXPORT Material represents all the data from a single bpy.Types.Material
    """

    BSDF_NODE_NAME = "Principled BSDF"
    NODE_TYPE_TEXTURE = "ShaderNodeTexImage"
    NODE_TYPE_NORMAL_MAP = "ShaderNodeNormalMap"
    NODE_TYPE_SEPARATE_COLOR = "ShaderNodeSeparateColor"
    SUPPORTED_NODE_TYPES = {
        NODE_TYPE_TEXTURE,
        NODE_TYPE_NORMAL_MAP,
        NODE_TYPE_SEPARATE_COLOR,
    }
    SOCKET_TYPE_RGBA = "RGBA"
    SOCKET_TYPE_VALUE = "VALUE"
    SOCKET_TYPE_VECTOR = "VECTOR"
    SUPPORTED_SOCKET_TYPES = {
        SOCKET_TYPE_RGBA,
        SOCKET_TYPE_VALUE,
        SOCKET_TYPE_VECTOR,
    }
    # List of supported properties.
    # See: ./docs/PrincipledBSDF_attributes.md
    PROPERTY_BASECOLOR = "Base Color"
    PROPERTY_METALLIC = "Metallic"
    PROPERTY_ROUGHNESS = "Roughness"
    PROPERTY_ALPHA = "Alpha"
    PROPERTY_SPECULAR_IOR = "Specular IOR Level"
    PROPERTY_SPECULAR_TINT = "Specular Tint"
    PROPERTY_NORMAL = "Normal"
    # This property is extracted from the node itself, instead of the input sockets.
    ENABLE_MULTISCATTER_COMPENSATION = "Specular MultiScatter Compensation"
    OUT_PROP_TEXTURE_CHANNEL = "textureChannel"

    def __init__(self, slotIndex: int, name: str, bpyMaterial: bpy.types.Material):
        print(f"Material[{slotIndex}]={name}")
        self._slotIndex = slotIndex
        self._name = name
        self._data = {}  # The data to export.
        # We store here the name of the textures that are actually sampled per channel.
        # key: textureName. value: a list of color channel names like ["Red", "Green"]
        self._texturesSampledPerChannel = {}
        self._BuildParseFunctors()
        self._ParseBlenderMaterial(bpyMaterial)

    def __str__(self) -> str:
        return f"O3Material[{self._slotIndex}]'{self._name}'"

    def _BuildParseFunctors(self):
        # All of these functors return a dictionary.
        self._parseFunctors = {
            O3Material.PROPERTY_BASECOLOR: self._parseInputSocket,
            O3Material.PROPERTY_METALLIC: self._parseInputSocket,
            O3Material.PROPERTY_ROUGHNESS: self._parseInputSocket,
            O3Material.PROPERTY_ALPHA: self._parseInputSocket,
            O3Material.PROPERTY_SPECULAR_IOR: self._parseInputSocket,
            O3Material.PROPERTY_SPECULAR_TINT: self._parseInputSocket,
            O3Material.PROPERTY_NORMAL: self._parseInputSocket,
        }

    def _parseInputSocket(
        self, nodeSocket: bpy.types.NodeSocket, inoutDict: dict
    ) -> dict:
        """
        @returns a dictionary that looks like:
        {
            "type" : "RGBA" | "VALUE" | "VECTOR",
            "value" : float | list[float],
            "textureName" : "" | "some_name",
            "textureChannel" : "" | "Red" | "Green" | "Blue",
            // Other things like strength
            "strength" : float
        }
        More notes:
        "textureName": If not empty, the "value" key is irrelevant. Contains the Blender packed texture name.
        "textureChannel": Only relevant if "textureName" is not empty, contains the color channel that should be sampled:
                          "Red" | "Green" | "Blue" | "Alpha",
        """
        if not (nodeSocket.type in O3Material.SUPPORTED_SOCKET_TYPES):
            print(f"Unsupported NodeSocket type '{nodeSocket.type}' for NodeSocket:")
            O3Material._DumpNodeSocketInfo(nodeSocket)
            return inoutDict
        inoutDict["type"] = nodeSocket.type
        if nodeSocket.type == O3Material.SOCKET_TYPE_VALUE:
            inoutDict["value"] = float(nodeSocket.default_value)
        else:
            inoutDict["value"] = tuple(mathutils.Vector(nodeSocket.default_value))
        if not nodeSocket.is_linked:
            return inoutDict
        # Check the type of the node this socket is connected to:
        # link: bpy.types.NodeLink = nodeSocket.links[0]
        link = nodeSocket.links[0]
        fromNode = link.from_node
        fromNodeType = fromNode.bl_idname
        if not (fromNodeType in O3Material.SUPPORTED_NODE_TYPES):
            print(f"Unsupported nodeType='{fromNodeType}'")
            return inoutDict
        if fromNodeType == O3Material.NODE_TYPE_TEXTURE:
            return self._ParseTextureNode(fromNode, inoutDict)
        elif fromNodeType == O3Material.NODE_TYPE_NORMAL_MAP:
            return self._ParseNormapMapNode(fromNode, link, inoutDict)
        elif fromNodeType == O3Material.NODE_TYPE_SEPARATE_COLOR:
            return self._ParseSeparateColorNode(fromNode, link, inoutDict)
        return inoutDict  # Should never arrive here.

    def _ParseTextureNode(self, fromNode: bpy.types.Node, inoutDict: dict) -> dict:
        """
        Inserts the property "textureName" in @inoutDict
        @returns The modified input dictionary
        """
        try:
            if fromNode.image is None:
                print(
                    f"Node with name '{fromNode.name}' and type '{fromNode.bl_idname}' doesn't have an image!"
                )
                return inoutDict
        except Exception:
            print(
                f"Node with name '{fromNode.name}' and type '{fromNode.bl_idname}' doesn't have an image property!"
            )
            return inoutDict
        inoutDict["textureName"] = fromNode.image.name
        return inoutDict

    def _ParseNormapMapNode(
        self, fromNode: bpy.types.Node, nodeLink: bpy.types.NodeLink, inoutDict: dict
    ) -> dict:
        """
        Inserts the properties "strength" and "textureName" in @inoutDict
        @returns The modified input dictionary
        """
        strength = 1.0
        for idx, inputSocket in enumerate(fromNode.inputs):
            if inputSocket.name == "Strength":
                strength = float(inputSocket.default_value)
                continue
            if inputSocket.name == "Color":
                if not inputSocket.is_linked:
                    print(
                        f"Was expecting the NormalMapNode to be linked to a texture node[{idx}]:"
                    )
                    O3Material._DumpNodeSocketInfo(inputSocket)
                else:
                    firstLink = O3Material._GetFirstLinkAtSocket(inputSocket)
                    self._ParseTextureNode(firstLink.from_node, inoutDict)
        inoutDict["strength"] = strength
        return inoutDict

    def _ParseSeparateColorNode(
        self, fromNode: bpy.types.Node, nodeLink: bpy.types.NodeLink, inoutDict: dict
    ) -> dict:
        """
        Inserts the properties "textureName" and "textureChannel" in @inoutDict
        @returns The modified input dictionary
        """
        inoutDict[O3Material.OUT_PROP_TEXTURE_CHANNEL] = nodeLink.from_socket.name
        for idx, inputSocket in enumerate(fromNode.inputs):
            if inputSocket.name == "Color":
                if not inputSocket.is_linked:
                    print(
                        f"Was expecting the SeparateColorNode to be linked to a texture node[{idx}]:"
                    )
                    O3Material._DumpNodeSocketInfo(inputSocket)
                else:
                    firstLink = O3Material._GetFirstLinkAtSocket(inputSocket)
                    self._ParseTextureNode(firstLink.from_node, inoutDict)
        if "textureName" in inoutDict:
            self._MarkTextureSampledPerChannel(
                inoutDict["textureName"], inoutDict[O3Material.OUT_PROP_TEXTURE_CHANNEL]
            )

        return inoutDict

    def _MarkTextureSampledPerChannel(self, textureName: str, textureChannel: str):
        if textureName == "" or textureChannel == "":
            return
        if textureChannel == "Red":
            return
        if not (textureName in self._texturesSampledPerChannel):
            self._texturesSampledPerChannel[textureName] = set()
        self._texturesSampledPerChannel[textureName].add(textureChannel)

    @staticmethod
    def _DumpNodeSocketInfo(nodeSocket: bpy.types.NodeSocket):
        linkCount = 0
        if nodeSocket.is_linked:
            linkCount = len(nodeSocket.links)
        print(
            f"NodeSocket name='{nodeSocket.name}'\n\tidentifier='{nodeSocket.identifier}',\n\tdefault_value='{nodeSocket.default_value}',\n\tlink_limit='{nodeSocket.link_limit}',\n\ttype='{nodeSocket.type}',\n\tnumLinks='{linkCount}'\n"
        )

    @staticmethod
    def _GetBpyNodeByName(nodeList: bpy.types.Nodes, name: str) -> bpy.types.Node:
        for node in nodeList:
            if node.name == name:
                return node
        return None

    @staticmethod
    def _GetFirstLinkAtSocket(nodeSocket: bpy.types.NodeSocket) -> bpy.types.NodeLink:
        link = nodeSocket.links[0]
        return link

    def _ParseMainMaterialNode(self, materialNode: bpy.types.Node):
        # DumpNodeInputs("  ", materialNode)
        if (
            materialNode.distribution == "MULTI_GGX"
        ):  # The alternative is 'GGX' (which means do not enable multiscatter compensation)
            self._data[O3Material.ENABLE_MULTISCATTER_COMPENSATION] = {"value": 1.0}
        for idx, inputSocket in enumerate(materialNode.inputs):
            if inputSocket.name in self._parseFunctors:
                O3Material._DumpNodeSocketInfo(inputSocket)
                funktor = self._parseFunctors[inputSocket.name]
                dataTable = {}
                dataTable = funktor(inputSocket, dataTable)
                self._data[inputSocket.name] = dataTable
            else:
                print(f"Can't Parse Input Socket: [{idx}]:{inputSocket.name}:")
                O3Material._DumpNodeSocketInfo(inputSocket)

    def _ParseBlenderMaterial(self, bpyMaterial: bpy.types.Material):
        if not bpyMaterial.use_nodes:
            raise Exception(f"{self} Doesn't use nodes!")
        nodeTree = bpyMaterial.node_tree
        print(f"NodeTree Type={nodeTree.type}")
        # for shaderNode in nodeTree.nodes:
        #    print(f"{indentation}node Name={shaderNode.name}, Label={shaderNode.label}")
        mainMaterialNode = O3Material._GetBpyNodeByName(
            nodeTree.nodes, O3Material.BSDF_NODE_NAME
        )
        if mainMaterialNode is None:
            print(
                f"WARNING: {self} Doesn't have the '{O3Material.BSDF_NODE_NAME}' node"
            )
            return
        self._ParseMainMaterialNode(mainMaterialNode)

    def GetSlotIndex(self) -> int:
        return self._slotIndex

    def GetName(self) -> str:
        return self._name

    def BuildTextureList(self) -> list[textureasset.TextureAsset]:
        """
        @returns A list of all TextureAssets found in this material.
        """
        retList = []
        textureNameList = _get_values_from_keys_with_name(self._data, "textureName")
        textureNameSet = set(textureNameList)
        textureNameList = list(textureNameSet)
        for textureName in textureNameList:
            newTexAsset = textureasset.TextureAsset(textureName)
            if textureName in self._texturesSampledPerChannel:
                newTexAsset._sampledChannels = self._texturesSampledPerChannel[
                    textureName
                ]
            retList.append(newTexAsset)
        return retList

    def GetDataAsJsonString(self) -> str:
        jsonStr = json.dumps(self._data, indent=4)
        return jsonStr

    def _GetSanitizedTexturePath(
        self, posixAssetsRelativeTexturePath: str, textureName: str, colorChannel: str
    ) -> str:
        if textureName == "":
            return textureName
        if colorChannel == "":
            # This is a regular texture that is sampled for all available color channels
            sanitizedTextureName = self.texturesDictionary[
                textureName
            ].GetSanitizedName()
        else:
            # This is a per channel sampled texture.
            # We need to figure out the path in which the new sampled texture was created.
            sanitizedTextureName = fileutils.GetResampledSanitizedFilenameExtension(
                self.texturesDictionary[textureName].GetSanitizedName(), colorChannel
            )
        sanitizedTexturePath = posixpath.join(
            PROJECT_ROOT, posixAssetsRelativeTexturePath, sanitizedTextureName
        )
        return sanitizedTexturePath

    # https://github.com/o3de/o3de/blob/development/Gems/Atom/Feature/Common/Assets/Materials/Types/MaterialInputs/BaseColorPropertyGroup.json
    def _AddO3deBaseColorProperty(
        self, srcDict: dict, posixAssetsRelativeTexturePath: str, dstDict: dict
    ):
        for k, v in srcDict.items():
            if k == "value":
                dstDict["baseColor.color"] = v
                continue
            if k == "textureName" and len(v) > 0:
                textureName = v
                colorChannel = (
                    srcDict[O3Material.OUT_PROP_TEXTURE_CHANNEL]
                    if O3Material.OUT_PROP_TEXTURE_CHANNEL in srcDict
                    else ""
                )
                dstDict["baseColor.textureMap"] = self._GetSanitizedTexturePath(
                    posixAssetsRelativeTexturePath, textureName, colorChannel
                )

    # https://github.com/o3de/o3de/blob/development/Gems/Atom/Feature/Common/Assets/Materials/Types/MaterialInputs/MetallicPropertyGroup.json
    def _AddO3deMetallicProperty(
        self, srcDict: dict, posixAssetsRelativeTexturePath: str, dstDict: dict
    ):
        for k, v in srcDict.items():
            if k == "value":
                dstDict["metallic.factor"] = v
                continue
            if k == "textureName":
                if len(v) > 0:
                    textureName = v
                    colorChannel = (
                        srcDict[O3Material.OUT_PROP_TEXTURE_CHANNEL]
                        if O3Material.OUT_PROP_TEXTURE_CHANNEL in srcDict
                        else ""
                    )
                    dstDict["metallic.textureMap"] = self._GetSanitizedTexturePath(
                        posixAssetsRelativeTexturePath, textureName, colorChannel
                    )
                    dstDict["metallic.useTexture"] = True
                else:
                    dstDict["metallic.useTexture"] = False

    # https://github.com/o3de/o3de/blob/development/Gems/Atom/Feature/Common/Assets/Materials/Types/MaterialInputs/RoughnessPropertyGroup.json
    def _AddO3deRoughnessProperty(
        self, srcDict: dict, posixAssetsRelativeTexturePath: str, dstDict: dict
    ):
        for k, v in srcDict.items():
            if k == "value":
                dstDict["roughness.factor"] = v
                continue
            if k == "textureName":
                if len(v) > 0:
                    textureName = v
                    colorChannel = (
                        srcDict[O3Material.OUT_PROP_TEXTURE_CHANNEL]
                        if O3Material.OUT_PROP_TEXTURE_CHANNEL in srcDict
                        else ""
                    )
                    dstDict["roughness.textureMap"] = self._GetSanitizedTexturePath(
                        posixAssetsRelativeTexturePath, textureName, colorChannel
                    )
                    dstDict["roughness.useTexture"] = True
                else:
                    dstDict["roughness.useTexture"] = False

    # https://github.com/o3de/o3de/blob/development/Gems/Atom/Feature/Common/Assets/Materials/Types/MaterialInputs/NormalPropertyGroup.json
    def _AddO3deNormalMapProperty(
        self, srcDict: dict, posixAssetsRelativeTexturePath: str, dstDict: dict
    ):
        for k, v in srcDict.items():
            if k == "strength":
                dstDict["normal.factor"] = v
                continue
            if k == "textureName":
                if len(v) > 0:
                    textureName = v
                    colorChannel = (
                        srcDict[O3Material.OUT_PROP_TEXTURE_CHANNEL]
                        if O3Material.OUT_PROP_TEXTURE_CHANNEL in srcDict
                        else ""
                    )
                    dstDict["normal.textureMap"] = self._GetSanitizedTexturePath(
                        posixAssetsRelativeTexturePath, textureName, colorChannel
                    )
                    dstDict["normal.useTexture"] = True
                else:
                    dstDict["normal.useTexture"] = False

    def _AddO3deNormalFlipChannelsProperties(
        self, normalFlipXChannel: bool, normalFlipYChannel: bool, dstDict: dict
    ):
        dstDict["normal.flipX"] = normalFlipXChannel
        dstDict["normal.flipY"] = normalFlipYChannel

    # https://github.com/o3de/o3de/blob/development/Gems/Atom/Feature/Common/Assets/Materials/Types/MaterialInputs/OpacityPropertyGroup.json
    def _AddO3deAlphaProperty(
        self, srcDict: dict, posixAssetsRelativeTexturePath: str, dstDict: dict
    ):
        for k, v in srcDict.items():
            if k == "value":
                dstDict["opacity.factor"] = v
                if v > 0.98:
                    dstDict["opacity.mode"] = "Opaque"
                else:
                    dstDict["opacity.mode"] = "Blended"
                continue
            if k == "textureName":
                if len(v) > 0:
                    textureName = v
                    colorChannel = (
                        srcDict[O3Material.OUT_PROP_TEXTURE_CHANNEL]
                        if O3Material.OUT_PROP_TEXTURE_CHANNEL in srcDict
                        else ""
                    )
                    dstDict["opacity.textureMap"] = self._GetSanitizedTexturePath(
                        posixAssetsRelativeTexturePath, textureName, colorChannel
                    )
                    dstDict["opacity.useTexture"] = True
                else:
                    dstDict["opacity.useTexture"] = False

    # https://github.com/o3de/o3de/blob/development/Gems/Atom/Feature/Common/Assets/Materials/Types/MaterialInputs/SpecularPropertyGroup.json
    def _AddO3deSpecularF0Property(
        self, srcDict: dict, posixAssetsRelativeTexturePath: str, dstDict: dict
    ):
        for k, v in srcDict.items():
            if k == "value":
                dstDict["specularF0.factor"] = v
                continue

    # https://github.com/o3de/o3de/blob/development/Gems/Atom/Feature/Common/Assets/Materials/Types/MaterialInputs/SpecularPropertyGroup.json
    def _AddO3deSpecularColorProperty(
        self, srcDict: dict, posixAssetsRelativeTexturePath: str, dstDict: dict
    ):
        """
        Applicable for Metals only, because dielectrics only reflect shades of white
        """
        for k, v in srcDict.items():
            if k == "color":
                continue  # Nothing to do here.
            if k == "textureName" and len(v) > 0:
                textureName = v
                colorChannel = (
                    srcDict[O3Material.OUT_PROP_TEXTURE_CHANNEL]
                    if O3Material.OUT_PROP_TEXTURE_CHANNEL in srcDict
                    else ""
                )
                dstDict["specularF0.textureMap"] = self._GetSanitizedTexturePath(
                    posixAssetsRelativeTexturePath, textureName, colorChannel
                )
                dstDict["specularF0.useTexture"] = True
            else:
                dstDict["specularF0.useTexture"] = False

    # https://github.com/o3de/o3de/blob/development/Gems/Atom/Feature/Common/Assets/Materials/Types/MaterialInputs/SpecularPropertyGroup.json
    def _AddO3deMultiscatterCompensationProperty(
        self, srcDict: dict, posixAssetsRelativeTexturePath: str, dstDict: dict
    ):
        for k, v in srcDict.items():
            if k == "value":
                if v > 0.5:
                    dstDict["specularF0.enableMultiScatterCompensation"] = True

    # https://github.com/o3de/o3de/blob/development/Gems/Atom/Feature/Common/Assets/Materials/Types/StandardPBR.materialtype
    # https://github.com/o3de/o3de/tree/development/Gems/Atom/Feature/Common/Assets/Materials/Types/MaterialInputs
    def GetDataAsO3DEMaterial(self, posixAssetsRelativeTexturePath: str) -> dict:
        o3deMaterial = {
            "materialType": "@gemroot:Atom_Feature_Common@/Assets/Materials/Types/StandardPBR.materialtype",
            "materialTypeVersion": 5,
            "propertyValues": {},
        }
        propertyValues = o3deMaterial["propertyValues"]
        for key, valueDict in self._data.items():
            match key:
                case O3Material.PROPERTY_BASECOLOR:
                    self._AddO3deBaseColorProperty(
                        valueDict, posixAssetsRelativeTexturePath, propertyValues
                    )
                case O3Material.PROPERTY_METALLIC:
                    self._AddO3deMetallicProperty(
                        valueDict, posixAssetsRelativeTexturePath, propertyValues
                    )
                case O3Material.PROPERTY_ROUGHNESS:
                    self._AddO3deRoughnessProperty(
                        valueDict, posixAssetsRelativeTexturePath, propertyValues
                    )
                case O3Material.PROPERTY_ALPHA:
                    self._AddO3deAlphaProperty(
                        valueDict, posixAssetsRelativeTexturePath, propertyValues
                    )
                case O3Material.PROPERTY_SPECULAR_IOR:
                    self._AddO3deSpecularF0Property(
                        valueDict, posixAssetsRelativeTexturePath, propertyValues
                    )
                case O3Material.PROPERTY_SPECULAR_TINT:  # Applicable for Metals only, because dielectrics only reflect shades of white
                    self._AddO3deSpecularColorProperty(
                        valueDict, posixAssetsRelativeTexturePath, propertyValues
                    )
                case O3Material.ENABLE_MULTISCATTER_COMPENSATION:
                    self._AddO3deMultiscatterCompensationProperty(
                        valueDict, posixAssetsRelativeTexturePath, propertyValues
                    )
                case O3Material.PROPERTY_NORMAL:
                    self._AddO3deNormalMapProperty(
                        valueDict, posixAssetsRelativeTexturePath, propertyValues
                    )
                    self._AddO3deNormalFlipChannelsProperties(
                        self.normalFlipXChannel, self.normalFlipYChannel, propertyValues
                    )
        return o3deMaterial

    def GetDataAsO3DEMaterialJsonString(
        self, posixAssetsRelativeTexturePath: str
    ) -> str:
        o3deMaterialDict = self.GetDataAsO3DEMaterial(posixAssetsRelativeTexturePath)
        jsonStr = json.dumps(o3deMaterialDict, indent=4)
        return jsonStr


def GetMaterialsFromObject(obj: bpy.types.Object) -> list[O3Material]:
    retList = []
    parsedMaterials = {}  # key: materialName, value: O3Material
    for materialSlot in obj.material_slots:
        if materialSlot.material is None:
            continue
        if materialSlot.name in parsedMaterials:
            # raise Exception(
            #    f"O3DEXPORT: Warning! For slot {materialSlot.slot_index}, a material with name '{materialSlot.name}' already exists at slot {parsedMaterials[materialSlot.name].GetSlotIndex()}"
            # )
            o3material = parsedMaterials[materialSlot.name]
            print(
                f"WARNING For slot {materialSlot.slot_index}, a material with name '{materialSlot.name}' already exists at slot {o3material.GetSlotIndex()}"
            )

        else:
            o3material = O3Material(
                materialSlot.slot_index, materialSlot.name, materialSlot.material
            )
            parsedMaterials[materialSlot.name] = o3material
        retList.append(o3material)
    return retList


def SaveAsO3DEMaterial(
    o3material: O3Material,
    filePath: str,
    assetsRelativeTexturePath: str,
    normalFlipXChannel: bool,
    normalFlipYChannel: bool,
) -> bool:
    try:
        o3material.normalFlipXChannel = normalFlipXChannel
        o3material.normalFlipYChannel = normalFlipYChannel
        assetsRelativeTexturePath = assetsRelativeTexturePath.replace(
            os.sep, posixpath.sep
        )
        with open(filePath, "w") as file:
            o3deJsonStr = o3material.GetDataAsO3DEMaterialJsonString(
                assetsRelativeTexturePath
            )
            file.write(o3deJsonStr)
    except Exception as e:
        print(
            f"Error trying to save as O3DE material '{o3material.GetName()}' at path '{filePath}'. Error: {e}"
        )
        return False
    return True


def SaveMaterial(o3material: O3Material, filePath: str) -> bool:
    """
    Useful for debugging purposes.
    """
    try:
        with open(filePath, "w") as file:
            o3deJsonStr = o3material.GetDataAsJsonString()
            file.write(o3deJsonStr)
    except Exception as e:
        print(
            f"Error trying to save material '{o3material.GetName()}' at path '{filePath}'. Error: {e}"
        )
        return False
    return True
