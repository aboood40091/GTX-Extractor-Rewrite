from ..dds import DDSHeader

from .gx2Enum import GX2CompSel
from .gx2Enum import GX2SurfaceFormat

from .gx2Texture import GX2TexturePrintInfo
from .gx2Texture import Linear2DToGX2Texture

# pypng
from png import Reader as png_reader


def PNGToGX2Texture(filenames, surfMode, perfModulation, tileMode, swizzle, SRGB, compSelIdx, printInfo=True):
    # Read the base image (level 0)
    reader = png_reader(filename=filenames.pop(0))
    baseWidth, baseHeight, rows, info = reader.asRGBA8()

    imageData = bytearray(pixel for row in rows for pixel in row)
    mipData = bytearray()

    # Read the remaining levels
    for i, name in enumerate(filenames):
        # Don't allow more than 13 mipmaps
        mipLevel = i + 1
        if mipLevel > 13:
            break

        reader = png_reader(filename=name)
        width, height, rows, info = reader.asRGBA8()

        # Make sure they are in order and the correct size
        assert width == max(1, baseWidth >> mipLevel)
        assert height == max(1, baseHeight >> mipLevel)

        mipData += bytearray(pixel for row in rows for pixel in row)

    del reader

    width = baseWidth
    height = baseHeight
    numMips = 1 + len(filenames)

    # TODO: RGBA8, for now
    format_ = GX2SurfaceFormat.SRGB_RGBA8 if SRGB else GX2SurfaceFormat.Unorm_RGBA8
    compSelArr = (GX2CompSel.Component.Red,
                  GX2CompSel.Component.Green,
                  GX2CompSel.Component.Blue,
                  GX2CompSel.Component.Alpha,
                  GX2CompSel.Component.Zero,
                  GX2CompSel.Component.One)

    # Combine the component selectors read from the input files and the user
    compSel = (compSelArr[compSelIdx[0]] << 24 |  \
               compSelArr[compSelIdx[1]] << 16 |  \
               compSelArr[compSelIdx[2]] << 8  |  \
               compSelArr[compSelIdx[3]])

    # Add the texture to the GFD file
    texture = Linear2DToGX2Texture(
        width, height, numMips, format_, compSel, imageData,
        tileMode, swizzle, mipData, surfMode, perfModulation,
    )

    # Print debug info if specified
    if printInfo:
        GX2TexturePrintInfo(texture)

    return texture
