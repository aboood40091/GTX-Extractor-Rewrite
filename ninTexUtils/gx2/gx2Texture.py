import struct

from .gx2Enum import GX2AAMode
from .gx2Enum import GX2CompSel
from .gx2Enum import GX2SurfaceDim
from .gx2Enum import GX2SurfaceUse
from .gx2Enum import GX2TileMode

from .gx2Surface import GX2Surface
from .gx2Surface import GX2SurfacePrintInfo

from ._texture_registers import calcRegs


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
        assert self.surface.use & GX2SurfaceUse.Texture

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

    def initTextureRegs(self, surfMode=0, perfModulation=7):
        self.regs = list(calcRegs(
            self.surface.width, self.surface.height, self.surface.numMips, self.surface.format,
            self.surface.tileMode, self.surface.pitch * (4 if self.surface.format.isCompressed() else 1),
            GX2CompSel.getCompSelAsArray(self.compSel), surfMode, perfModulation,
        ))

    @staticmethod
    def initTexture(dim, width, height, depth, numMips, format_, compSel, tileMode=GX2TileMode.Default,
                    swizzle=0, surfMode=0, perfModulation=7):

        texture = GX2Texture()

        texture.surface.dim = dim
        texture.surface.width = width
        texture.surface.height = height
        texture.surface.depth = depth
        texture.surface.numMips = numMips
        texture.surface.format = format_
        texture.surface.tileMode = tileMode
        texture.surface.swizzle = swizzle << 8

        texture.surface.calcSurfaceSizeAndAlignment()

        texture.viewFirstMip = 0
        texture.viewNumMips = numMips
        texture.viewFirstSlice = 0
        texture.viewNumSlices = depth
        texture.compSel = compSel

        texture.initTextureRegs(surfMode, perfModulation)

        return texture


def GX2TexturePrintInfo(texture):
    GX2SurfacePrintInfo(texture.surface)

    compSel = tuple(GX2CompSel.getComponent(texture.compSel, i) for i in range(4))

    print()
    print("// ----- GX2 Component Selectors ----- ")
    print("  Red Channel     =", repr(compSel[0]))
    print("  Green Channel   =", repr(compSel[1]))
    print("  Blue Channel    =", repr(compSel[2]))
    print("  Alpha Channel   =", repr(compSel[3]))


def Linear2DToGX2Texture(width, height, numMips, format_, compSel, imageData, tileMode=GX2TileMode.Default,
                         swizzle=0, mipData=b'', surfMode=0, perfModulation=7):

    # Create a new GX2Texture to store the untiled texture
    linear_texture = GX2Texture.initTexture(
        GX2SurfaceDim.Dim2D, width, height, 1,
        numMips, format_, compSel,
        GX2TileMode.Linear_Special,
    )

    # Validate and set the image data
    imageData = bytes(imageData)
    assert len(imageData) >= linear_texture.surface.imageSize
    linear_texture.surface.imageData = imageData[:linear_texture.surface.imageSize]

    # Validate and set the mip data
    if numMips > 1:
        mipData = bytes(mipData)
        assert len(mipData) >= linear_texture.surface.mipSize
        linear_texture.surface.mipData = mipData[:linear_texture.surface.mipSize]

    # Create a new GX2Texture to store the tiled texture
    texture = GX2Texture.initTexture(
        GX2SurfaceDim.Dim2D, width, height, 1,
        numMips, format_, compSel, tileMode,
        swizzle, surfMode, perfModulation,
    )

    # Tile our texture
    GX2Surface.copySurface(linear_texture.surface, texture.surface)

    return texture
