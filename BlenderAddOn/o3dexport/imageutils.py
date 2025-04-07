"""
Copyright (c) Contributors to the Open 3D Engine Project.
For complete copyright and license terms please see the LICENSE at the root of this distribution.

SPDX-License-Identifier: Apache-2.0 OR MIT
"""

# Created by Galib Arrieta (aka galibzon@github, lumbermixalot@github)
# under contract with Meta Platforms, Inc.
# Donated by Meta Platforms, Inc as an open source project.

#import numpy as np
#from PIL import Image

import OpenImageIO as oiio

def LoadImageFileAsImageBuf(imageFilePath: str) -> oiio.ImageBuf:
    return oiio.ImageBuf(imageFilePath)

def CreateImageBufFromColorChannel(imageBuf: oiio.ImageBuf, channel: int) -> oiio.ImageBuf:
    singleChannelImageBuf = oiio.ImageBugAlgo.channels(imageBuf, (channel,))
    return singleChannelImageBuf

# Old version using PIL, but required manual installation of `pillow`
# inside Python for Blender. See newer version with OpenImageIO which ships
# with Blender.
# def LoadImageFileAsArray(imageFilePath: str) -> np.array:
#     img = Image.open(imageFilePath)
#     imageArray = np.array(img)
#     return imageArray
# 
# 
# def CreateImageFromColorChannel(imageArray: np.array, channel: int) -> Image:
#     selectedChannelArray = imageArray[:, :, channel]
#     newImg = Image.fromarray(selectedChannelArray)
#     return newImg
#
