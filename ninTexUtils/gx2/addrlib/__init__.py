#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Addrlib
# Copyright © 2018 AboodXD

# Addrlib
# A Python/Cython Texture Address Library for Wii U textures.

from ..._cython import is_available as _is_cython_available


if _is_cython_available:
    from . import addrlib_cy as addrlib

else:
    from . import addrlib


# Define the functions that can be used
getDefaultGX2TileMode = addrlib.getDefaultGX2TileMode
deswizzle = addrlib.deswizzle
swizzle = addrlib.swizzle
surfaceGetBitsPerPixel = addrlib.surfaceGetBitsPerPixel
getSurfaceInfo = addrlib.getSurfaceInfo
