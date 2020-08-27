import struct

from gx2Enum import GX2AAMode, GX2SurfaceUse, GX2TileMode, GX2CompSel
from gx2Surface import GX2Surface
from texRegisters import calcRegs


class GX2Texture:
    _sFormat = '>%dx10I' % GX2Surface.size()

    def __init__(self, data=None, pos=0):
        self.surface = GX2Surface()
        self.viewFirstMip = 0
        self.viewNumMips = 1
        self.viewFirstSlice = 0
        self.viewNumSlices = 1
        self.compSel = GX2CompSel.ZZZO
        self.regs = [0 for _ in range(5)]

        if data:
            self.load(data, pos)

    def load(self, data, pos=0):
        self.surface.load(data, pos)

        assert self.surface.aa == GX2AAMode.Mode1X
        assert self.surface.use.value & GX2SurfaceUse.Texture.value

        (self.viewFirstMip,
         self.viewNumMips,
         self.viewFirstSlice,
         self.viewNumSlices,
         self.compSel,
         *self.regs) = struct.unpack_from(self._sFormat, data, pos)

        if self.viewNumMips == 0:
            self.viewNumMips = 1

        if self.viewNumSlices == 0:
            self.viewNumSlices = 1

        assert 0 <= self.viewFirstMip <= self.surface.numMips - 1
        assert 1 <= self.viewNumMips <= self.surface.numMips - self.viewFirstMip
        assert 0 <= self.viewFirstSlice <= self.surface.depth - 1
        assert 1 <= self.viewNumSlices <= self.surface.depth - self.viewFirstSlice

    def save(self):
        surface = self.surface.save()
        texture = bytearray(struct.pack(
            self._sFormat,
            self.viewFirstMip,
            self.viewNumMips,
            self.viewFirstSlice,
            self.viewNumSlices,
            self.compSel,
            *self.regs,
        ))

        texture[:GX2Surface.size()] = surface

        return bytes(texture)

    @staticmethod
    def size():
        return GX2Surface.size() + 0x28

    def initTextureRegs(self, surfMode=0):
        self.regs = list(calcRegs(
            self.surface.width, self.surface.height, self.surface.numMips, self.surface.format.value,
            self.surface.tileMode.value, self.surface.pitch * (4 if self.surface.format.isBC() else 1),
            GX2CompSel.getCompSelAsArray(self.compSel), surfMode,
        ))

    @staticmethod
    def initTexture(dim, width, height, depth, numMips, format_, compSel, tileMode=GX2TileMode.Default, swizzle=0, surfMode=0):
        texture = GX2Texture()

        texture.surface.dim = dim
        texture.surface.width = width
        texture.surface.height = height
        texture.surface.depth = depth
        texture.surface.numMips = numMips
        texture.surface.format = format_
        texture.surface.tileMode = tileMode
        texture.surface.swizzle = swizzle

        texture.surface.calcSurfaceSizeAndAlignment()

        texture.viewFirstMip = 0
        texture.viewNumMips = numMips
        texture.viewFirstSlice = 0
        texture.viewNumSlices = depth
        texture.compSel = compSel

        texture.initTextureRegs(surfMode)

        return texture
