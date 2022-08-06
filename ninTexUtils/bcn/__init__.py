#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# DXT1/3/5 Decompressor
# Version 0.1
# Copyright © 2018 MasterVermilli0n / AboodXD

################################################################
################################################################

from .._cython import is_available as _is_cython_available


if _is_cython_available:
    from . import decompress_cy as _decompress

else:
    from . import decompress as _decompress


def decompressDXT1(data, width, height):
    if not isinstance(data, bytes):
        try:
            data = bytes(data)

        except Exception:
            print("Couldn't decompress data")
            return b''

    csize = ((width + 3) // 4) * ((height + 3) // 4) * 8
    if len(data) < csize:
        print("Compressed data is incomplete")
        return b''

    data = data[:csize]
    return _decompress.decompressDXT1(data, width, height)


def decompressDXT3(data, width, height):
    if not isinstance(data, bytes):
        try:
            data = bytes(data)

        except Exception:
            print("Couldn't decompress data")
            return b''

    csize = ((width + 3) // 4) * ((height + 3) // 4) * 16
    if len(data) < csize:
        print("Compressed data is incomplete")
        return b''

    data = data[:csize]
    return _decompress.decompressDXT3(data, width, height)


def decompressDXT5(data, width, height):
    if not isinstance(data, bytes):
        try:
            data = bytes(data)

        except Exception:
            print("Couldn't decompress data")
            return b''

    csize = ((width + 3) // 4) * ((height + 3) // 4) * 16
    if len(data) < csize:
        print("Compressed data is incomplete")
        return b''

    data = data[:csize]
    return _decompress.decompressDXT5(data, width, height)


def decompressBC4(data, width, height, SNORM=0):
    if not isinstance(data, bytes):
        try:
            data = bytes(data)

        except Exception:
            print("Couldn't decompress data")
            return b''

    csize = ((width + 3) // 4) * ((height + 3) // 4) * 8
    if len(data) < csize:
        print("Compressed data is incomplete")
        return b''

    data = data[:csize]
    return _decompress.decompressBC4(data, width, height, SNORM)


def decompressBC5(data, width, height, SNORM=0):
    if not isinstance(data, bytes):
        try:
            data = bytes(data)

        except Exception:
            print("Couldn't decompress data")
            return b''

    csize = ((width + 3) // 4) * ((height + 3) // 4) * 16
    if len(data) < csize:
        print("Compressed data is incomplete")
        return b''

    data = data[:csize]
    return _decompress.decompressBC5(data, width, height, SNORM)
