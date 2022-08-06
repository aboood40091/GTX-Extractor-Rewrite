#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright © 2018 AboodXD
# Licensed under GNU GPLv3

def _register0(width, pitch, tileType, tileMode, dim):
    return ((width    & 0x1FFF) << 19 |  \
            (pitch    & 0x07FF) << 8  |  \
            (tileType & 0x0001) << 7  |  \
            (tileMode & 0x000F) << 3  |  \
            (dim      & 0x0007))


def _register1(format_, depth, height):
    return ((format_ & 0x003F) << 26 |  \
            (depth   & 0x1FFF) << 13 |  \
            (height  & 0x1FFF))


def _register2(baseLevel, dstSelW, dstSelZ, dstSelY, dstSelX, requestSize, endian, forceDegamma, surfMode, numFormat, formatComp):
    return ((baseLevel    & 7) << 28 |  \
            (dstSelW      & 7) << 25 |  \
            (dstSelZ      & 7) << 22 |  \
            (dstSelY      & 7) << 19 |  \
            (dstSelX      & 7) << 16 |  \
            (requestSize  & 3) << 14 |  \
            (endian       & 3) << 12 |  \
            (forceDegamma & 1) << 11 |  \
            (surfMode     & 1) << 10 |  \
            (numFormat    & 3) << 8  |  \
            (formatComp   & 3) << 6  |  \
            (formatComp   & 3) << 4  |  \
            (formatComp   & 3) << 2  |  \
            (formatComp   & 3))


def _register3(yuvConv, lastArray, baseArray, lastLevel):
    return ((yuvConv   & 0x0003) << 30 |  \
            (lastArray & 0x1FFF) << 17 |  \
            (baseArray & 0x1FFF) << 4  |  \
            (lastLevel & 0x000F))


def _register4(type_, advisClampLOD, advisFaultLOD, interlaced, perfModulation, maxAnisoRatio, MPEGClamp):
    return ((type_          & 0x03) << 30 |  \
            (advisClampLOD  & 0x3F) << 13 |  \
            (advisFaultLOD  & 0x0F) << 9  |  \
            (interlaced     & 0x01) << 8  |  \
            (perfModulation & 0x07) << 5  |  \
            (maxAnisoRatio  & 0x07) << 2  |  \
            (MPEGClamp      & 0x03))


def calcRegs(width, height, numMips, format_, tileMode, pitch, compSel, surfMode, perfModulation):
    # register0
    pitch = max(pitch, 8)
    register0 = _register0(width - 1, (pitch // 8) - 1, 0, tileMode, 1)

    # register1
    register1 = _register1(format_, 0, height - 1)

    # register2
    formatComp = 0
    numFormat = 0
    forceDegamma = 0

    if format_ & 0x200:
        formatComp = 1

    if format_ & 0x800:
        numFormat = 2

    elif format_ & 0x100:
        numFormat = 1

    if format_ & 0x400:
        forceDegamma = 1

    register2 = _register2(0, compSel[3], compSel[2], compSel[1], compSel[0], 2, 0, forceDegamma, surfMode, numFormat, formatComp)

    # register3
    register3 = _register3(0, 0, 0, numMips - 1)

    # register4
    register4 = _register4(2, 0, 0, 0, perfModulation, 4, 0)

    return (
        register0,
        register1,
        register2,
        register3,
        register4,
    )
