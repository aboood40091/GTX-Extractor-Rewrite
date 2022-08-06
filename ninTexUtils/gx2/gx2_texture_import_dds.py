from ..dds import DDSHeader

from .gx2Enum import GX2CompSel
from .gx2Enum import GX2SurfaceFormat

from .gx2Texture import GX2TexturePrintInfo
from .gx2Texture import Linear2DToGX2Texture


fourCCs = {
    b'DXT1': (0x031, 0x08),
    b'DXT2': (0x032, 0x10),
    b'DXT3': (0x032, 0x10),
    b'DXT4': (0x033, 0x10),
    b'DXT5': (0x033, 0x10),
    b'ATI1': (0x034, 0x08),
    b'BC4U': (0x034, 0x08),
    b'BC4S': (0x234, 0x08),
    b'ATI2': (0x035, 0x10),
    b'BC5U': (0x035, 0x10),
    b'BC5S': (0x235, 0x10),
}

validComps = {
    0x08: {0x001: (0x000000ff,),
           0x002: (0x0000000f, 0x000000f0,)},
    0x10: {0x007: (0x000000ff, 0x0000ff00,),
           0x008: (0x0000001f, 0x000007e0, 0x0000f800,),
           0x00a: (0x0000001f, 0x000003e0, 0x00007c00, 0x00008000,),
           0x00b: (0x0000000f, 0x000000f0, 0x00000f00, 0x0000f000,)},
    0x20: {0x019: (0x3ff00000, 0x000ffc00, 0x000003ff, 0xc0000000,),
           0x01a: (0x000000ff, 0x0000ff00, 0x00ff0000, 0xff000000,)},
}


def DDSToGX2Texture(filename, surfMode, perfModulation, tileMode, swizzle, SRGB, compSelIdx, printInfo=True):
    # Read the whole file
    with open(filename, "rb") as inf:
        inb = inf.read()

    # Create a new DDSHeader object
    header = DDSHeader()

    # Parse the input file, throw an exception if reading failed
    try:
        header.load(inb)

    except Exception:
        raise RuntimeError("Not a valid DDS input file!") from None

    if header.depth > 1 or header.caps2 & DDSHeader.Caps2.Volume:
        raise NotImplementedError("3D textures are not supported!")

    if header.caps2 & (DDSHeader.Caps2.CubeMap |            \
                       DDSHeader.Caps2.CubeMap_PositiveX |  \
                       DDSHeader.Caps2.CubeMap_NegativeX |  \
                       DDSHeader.Caps2.CubeMap_PositiveY |  \
                       DDSHeader.Caps2.CubeMap_NegativeY |  \
                       DDSHeader.Caps2.CubeMap_PositiveZ |  \
                       DDSHeader.Caps2.CubeMap_NegativeZ):
        raise NotImplementedError("Cube Maps are not supported!")

    # Get misc. values
    width = header.width
    height = header.height
    numMips = header.mipMapCount

    # Make sure YUV is not being used
    if header.pixelFormat.flags & DDSHeader.PixelFormat.Flags.YUV:
        raise NotImplementedError("YUV color space is not supported!")

    # Treat uncompressed formats differently
    if not (header.pixelFormat.flags & DDSHeader.PixelFormat.Flags.FourCC):
        # Get and validate the bits-per-pixel
        bitsPerPixel = header.pixelFormat.rgbBitCount
        if bitsPerPixel not in validComps:
            raise RuntimeError("Unrecognized number of bits per pixel: %d" % bitsPerPixel)

        # Get the RGBA masks
        rMask = header.pixelFormat.rBitMask
        gMask = header.pixelFormat.gBitMask
        bMask = header.pixelFormat.bBitMask
        aMask = header.pixelFormat.aBitMask

        # Pixel format flags
        alphaOnly = header.pixelFormat.flags & DDSHeader.PixelFormat.Flags.Alpha
        hasAlpha = header.pixelFormat.flags & DDSHeader.PixelFormat.Flags.AlphaPixels
        RGB = header.pixelFormat.flags & DDSHeader.PixelFormat.Flags.RGB

        # Determine the optimal format and component selectors from the RGBA masks
        for format_, masks in validComps[bitsPerPixel].items():
            if alphaOnly:  # Alpha-only
                if aMask in masks:
                    compSelArr = (GX2CompSel.Component.One,
                                  GX2CompSel.Component.One,
                                  GX2CompSel.Component.One,
                                  masks.index(aMask),
                                  GX2CompSel.Component.Zero,
                                  GX2CompSel.Component.One)
                    break

            elif hasAlpha and RGB:  # RGBA
                if rMask in masks and gMask in masks and bMask in masks and aMask in masks:
                    compSelArr = (masks.index(rMask),
                                  masks.index(gMask),
                                  masks.index(bMask),
                                  masks.index(aMask),
                                  GX2CompSel.Component.Zero,
                                  GX2CompSel.Component.One)
                    break

            elif hasAlpha:  # LA (Luminance + Alpha)
                if rMask in masks and aMask in masks:
                    compSelArr = (masks.index(rMask),
                                  masks.index(rMask),
                                  masks.index(rMask),
                                  masks.index(aMask),
                                  GX2CompSel.Component.Zero,
                                  GX2CompSel.Component.One)
                    break

            elif RGB:  # RGB
                if rMask in masks and gMask in masks and bMask in masks:
                    compSelArr = (masks.index(rMask),
                                  masks.index(gMask),
                                  masks.index(bMask),
                                  GX2CompSel.Component.One,
                                  GX2CompSel.Component.Zero,
                                  GX2CompSel.Component.One)
                    break

            else:  # Luminance
                if rMask in masks:
                    compSelArr = (masks.index(rMask),
                                  masks.index(rMask),
                                  masks.index(rMask),
                                  GX2CompSel.Component.One,
                                  GX2CompSel.Component.Zero,
                                  GX2CompSel.Component.One)
                    break

        else:
            raise RuntimeError("Could not determine the texture format of the input DDS file!")

        # If determined format is RGBA8, check and add SRGB mask
        if format_ == 0x1a and SRGB:
            format_ |= 0x400
        format_ = GX2SurfaceFormat(format_)

        # Calculate imageSize for this level
        imageSize = width * height * (bitsPerPixel >> 3)

    else:
        # DX10 is not supported yet
        if header.pixelFormat.fourCC == b'DX10':
            raise NotImplementedError("DX10 DDS files are not supported!")

        # Validate FourCC
        elif header.pixelFormat.fourCC not in fourCCs:
            raise RuntimeError("Unrecognized FourCC: %s" % repr(header.pixelFormat.fourCC))

        # Determine the format and blockSize
        format_, blockSize = fourCCs[header.pixelFormat.fourCC]

        # DDS is incapable of letting you select the components for BCn
        if not (format_ & 4):
            # Determined format is BC1 or BC2 or BC3
            compSelArr = (GX2CompSel.Component.Red,
                          GX2CompSel.Component.Green,
                          GX2CompSel.Component.Blue,
                          GX2CompSel.Component.Alpha,
                          GX2CompSel.Component.Zero,
                          GX2CompSel.Component.One)

            # Check and add SRGB mask
            if SRGB:
                format_ |= 0x400

        elif (format_ & 0x3F) == 0x34:
            # Determined format is BC4
            compSelArr = (GX2CompSel.Component.Red,
                          GX2CompSel.Component.Zero,
                          GX2CompSel.Component.Zero,
                          GX2CompSel.Component.One,
                          GX2CompSel.Component.Zero,
                          GX2CompSel.Component.One)

        elif (format_ & 0x3F) == 0x35:
            # Determined format is BC5
            compSelArr = (GX2CompSel.Component.Red,
                          GX2CompSel.Component.Green,
                          GX2CompSel.Component.Zero,
                          GX2CompSel.Component.One,
                          GX2CompSel.Component.Zero,
                          GX2CompSel.Component.One)

        format_ = GX2SurfaceFormat(format_)

        # Calculate imageSize for this level
        imageSize = ((width + 3) >> 2) * ((height + 3) >> 2) * blockSize

    # Get imageData and mipData
    imageData = inb[DDSHeader.size():DDSHeader.size() + imageSize]
    mipData = inb[DDSHeader.size() + imageSize:]

    # Combine the component selectors read from the input files and the user
    compSel = (compSelArr[compSelIdx[0]] << 24 |  \
               compSelArr[compSelIdx[1]] << 16 |  \
               compSelArr[compSelIdx[2]] << 8  |  \
               compSelArr[compSelIdx[3]])

    # Create the texture
    texture = Linear2DToGX2Texture(
        width, height, numMips, format_, compSel, imageData,
        tileMode, swizzle, mipData, surfMode, perfModulation,
    )

    # Print debug info if specified
    if printInfo:
        GX2TexturePrintInfo(texture)

    return texture
