import struct

import addrlib
from gx2Enum import GX2SurfaceDim, GX2SurfaceFormat, GX2AAMode, GX2SurfaceUse, GX2TileMode
from util import roundUp, divRoundUp


class GX2Surface:
    _sFormat = '>29I'

    def __init__(self, data=None, pos=0):
        self.dim = GX2SurfaceDim.Dim2D
        self.width = 0
        self.height = 0
        self.depth = 1
        self.numMips = 1
        self.format = GX2SurfaceFormat.Invalid
        self.aa = GX2AAMode.Mode1X
        self.use = GX2SurfaceUse.Texture
        self.imageSize = 0
        self.imageData = b''
        self.mipSize = 0
        self.mipData = b''
        self.tileMode = GX2TileMode.Default
        self.swizzle = 0
        self.alignment = 0
        self.pitch = 0
        self.mipOffset = [0 for _ in range(13)]

        if data:
            self.load(data, pos)

    def load(self, data, pos=0):
        (dim,
         self.width,
         self.height,
         self.depth,
         self.numMips,
         format_,
         aa,
         use,
         self.imageSize,
         imagePtr,
         self.mipSize,
         mipPtr,
         tileMode,
         self.swizzle,
         self.alignment,
         self.pitch,
         *self.mipOffset) = struct.unpack_from(self._sFormat, data, pos)

        assert self.width != 0
        assert self.height != 0
        assert self.numMips <= 14
        assert self.imageSize != 0
        assert (self.mipSize != 0 if self.numMips > 1 else self.mipSize == 0)
        assert self.pitch != 0

        # Assertion must not fail for serialized GX2Surface
        assert format_ != GX2SurfaceFormat.Invalid.value
        assert imagePtr == 0
        assert mipPtr == 0
        assert tileMode != GX2TileMode.Default.value

        self.dim = GX2SurfaceDim(dim)
        self.format = GX2SurfaceFormat(format_)
        self.aa = GX2AAMode(aa)
        self.use = GX2SurfaceUse(use)
        self.tileMode = GX2TileMode(tileMode)

        if self.depth == 0:
            self.depth = 1

        if self.numMips == 0:
            self.numMips = 1

    def save(self):
        return struct.pack(
            self._sFormat,
            self.dim.value,
            self.width,
            self.height,
            self.depth,
            self.numMips,
            self.format.value,
            self.aa.value,
            self.use.value,
            self.imageSize,
            0,
            self.mipSize,
            0,
            self.tileMode.value,
            self.swizzle,
            self.alignment,
            self.pitch,
            *self.mipOffset,
        )

    @staticmethod
    def size():
        return 0x74

    def calcSurfaceSizeAndAlignment(self):
        # Calculate the best tileMode if set to default
        if self.tileMode == GX2TileMode.Default:
            self.tileMode = GX2TileMode(addrlib.getDefaultGX2TileMode(
                self.dim.value, self.width, self.height, self.depth,
                self.format.value, self.aa.value, self.use.value,
            ))

        # Calculate the surface info for the base level
        surfInfo = addrlib.getSurfaceInfo(
            self.format.value, self.width, self.height, self.depth,
            self.dim.value, self.tileMode.value, self.aa.value, 0,
        )

        # Set the image size, alignment and pitch
        self.imageSize = surfInfo.surfSize
        self.alignment = surfInfo.baseAlign
        self.pitch = surfInfo.pitch

        # TODO: set swizzle 1D tile level for tiled surfaces

        # Calculate the mip size and mip offsets
        self.mipSize = 0
        for mipLevel in range(1, self.numMips):
            # Calculate the surface info for the mip level
            surfInfo = addrlib.getSurfaceInfo(
                self.format.value, self.width, self.height, self.depth,
                self.dim.value, self.tileMode.value, self.aa.value, mipLevel,
            )

            # Make sure the level is aligned
            self.mipSize = roundUp(self.mipSize, surfInfo.baseAlign)

            # Set the offset of the level
            ## Level 1 offset is used to place the mip data (levels 1+) after the image data (level 0)
            ## The value is the minimum size of the image data + padding to ensure the mip data is aligned 
            if mipLevel == 1:
                # Level 1 alignment should suffice to ensure all the other levels are aligned as well
                self.mipOffset[0] = roundUp(self.imageSize, surfInfo.baseAlign)

            else:
                # Level offset should be the size of all previous levels (aligned)
                self.mipOffset[mipLevel - 1] = self.mipSize

            self.mipSize += surfInfo.surfSize

        # Clear the unused mip offsets
        for mipLevel in range(self.numMips, 14):
            self.mipOffset[mipLevel - 1] = 0

    @staticmethod
    def copySurface(src, dst):
        # Check requirements
        assert dst.dim == src.dim
        assert dst.width == src.width
        assert dst.height == src.height
        assert dst.depth <= src.depth
        assert dst.numMips <= src.numMips
        assert dst.format == src.format

        # Check if the two surfaces are the same
        if src.tileMode == dst.tileMode and (src.tileMode == GX2TileMode.Linear_Aligned
                                             or src.tileMode == GX2TileMode.Linear_Special
                                             or ((src.swizzle >> 8) & 7) == ((dst.swizzle >> 8) & 7)):
            # No need to process anything, just copy the data over
            dst.imageData = src.imageData[:dst.imageSize]
            dst.mipData = src.mipData[:dst.mipSize]
            return

        ### Untile the source data ###

        levels = []

        # Calculate the surface info for the base level
        surfInfo = addrlib.getSurfaceInfo(
            src.format.value, src.width, src.height, src.depth,
            src.dim.value, src.tileMode.value, src.aa.value, 0,
        )

        # Get the depth used for tiling
        tileMode = GX2TileMode(surfInfo.tileMode)
        tilingDepth = surfInfo.depth

        if tileMode in (GX2TileMode.Tiled_1D_Thick,
                        GX2TileMode.Tiled_2D_Thick, GX2TileMode.Tiled_2B_Thick,
                        GX2TileMode.Tiled_3D_Thick, GX2TileMode.Tiled_3B_Thick):
            tilingDepth = divRoundUp(tilingDepth, 4)

        # Depths higher than 1 are currently not supported
        assert tilingDepth == 1

        # Block width and height for the format
        blkWidth, blkHeight = (4, 4) if src.format.isBC() else (1, 1)

        # Bytes-per-pixel
        bpp = divRoundUp(surfInfo.bpp, 8)

        # Untile the base level
        result = addrlib.deswizzle(
            src.width, src.height, 1, src.format.value, 0, src.use.value, surfInfo.tileMode,
            src.swizzle, surfInfo.pitch, surfInfo.bpp, 0, 0, src.imageData,
        )

        # Make sure it's the correct size
        size = divRoundUp(src.width, blkWidth) * divRoundUp(src.height, blkHeight) * bpp
        assert len(result) >= size
        levels.append(result[:size])

        # Untile the other levels (mipmaps)
        offset = 0
        for mipLevel in range(1, src.numMips):
            # Calculate the width and height of the mip level
            width = max(1, src.width >> mipLevel)
            height = max(1, src.height >> mipLevel)

            # Calculate the surface info for the mip level
            surfInfo = addrlib.getSurfaceInfo(
                src.format.value, src.width, src.height, src.depth,
                src.dim.value, src.tileMode.value, src.aa.value, mipLevel,
            )

            # Untile the mip level
            result = addrlib.deswizzle(
                width, height, 1, src.format.value, 0, src.use.value, surfInfo.tileMode,
                src.swizzle, surfInfo.pitch, surfInfo.bpp, 0, 0, src.mipData[offset:offset + surfInfo.surfSize],
            )

            # Make sure it's the correct size
            size = divRoundUp(width, blkWidth) * divRoundUp(height, blkHeight) * bpp
            assert len(result) >= size
            levels.append(result[:size])

            # Set the offset of the next level
            if mipLevel < src.numMips - 1:
                offset = src.mipOffset[mipLevel]

        ### Tile the destination data ###

        # Calculate the surface info for the base level
        surfInfo = addrlib.getSurfaceInfo(
            dst.format.value, dst.width, dst.height, dst.depth,
            dst.dim.value, dst.tileMode.value, dst.aa.value, 0,
        )

        # Get the depth used for tiling
        tileMode = GX2TileMode(surfInfo.tileMode)
        tilingDepth = surfInfo.depth

        if tileMode in (GX2TileMode.Tiled_1D_Thick,
                        GX2TileMode.Tiled_2D_Thick, GX2TileMode.Tiled_2B_Thick,
                        GX2TileMode.Tiled_3D_Thick, GX2TileMode.Tiled_3B_Thick):
            tilingDepth = divRoundUp(tilingDepth, 4)

        # Depths higher than 1 are currently not supported
        assert tilingDepth == 1

        # Block width and height for the format
        blkWidth, blkHeight = (4, 4) if dst.format.isBC() else (1, 1)

        # Bytes-per-pixel
        bpp = divRoundUp(surfInfo.bpp, 8)

        # Tile the base level
        dst.imageData = addrlib.swizzle(
            dst.width, dst.height, 1, dst.format.value, 0, dst.use.value, surfInfo.tileMode,
            dst.swizzle, surfInfo.pitch, surfInfo.bpp, 0, 0, levels[0].ljust(surfInfo.surfSize, b'\0'),
        )[:surfInfo.surfSize]

        # Tile the other levels (mipmaps)
        dst.mipData = b''
        for mipLevel in range(1, dst.numMips):
            # Calculate the width and height of the mip level
            width = max(1, dst.width >> mipLevel)
            height = max(1, dst.height >> mipLevel)

            # Calculate the surface info for the mip level
            surfInfo = addrlib.getSurfaceInfo(
                dst.format.value, dst.width, dst.height, dst.depth,
                dst.dim.value, dst.tileMode.value, dst.aa.value, mipLevel,
            )

            if mipLevel != 1:
                dst.mipData += b'\0' * (dst.mipOffset[mipLevel - 1] - len(dst.mipData))

            # Untile the mip level
            dst.mipData += addrlib.swizzle(
                width, height, 1, dst.format.value, 0, dst.use.value, surfInfo.tileMode,
                dst.swizzle, surfInfo.pitch, surfInfo.bpp, 0, 0, levels[mipLevel].ljust(surfInfo.surfSize, b'\0'),
            )[:surfInfo.surfSize]
