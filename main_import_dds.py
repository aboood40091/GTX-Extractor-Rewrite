# Local libraries
from dds import DDSHeader
from gx2Enum import GX2SurfaceFormat, GX2CompSel
from gx2Texture import GX2TexturePrintInfo, Linear2DToGX2Texture
from importOptions import processArgv


fourCCs = {
    b'DXT1': (0x31, 8),
    b'DXT3': (0x32, 16),
    b'DXT5': (0x33, 16),
}

validComps = {
    0x08: {0x01: (0x000000ff,),
           0x02: (0x0000000f, 0x000000f0,)},
    0x10: {0x07: (0x000000ff, 0x0000ff00,),
           0x08: (0x0000001f, 0x000007e0, 0x0000f800,),
           0x0a: (0x0000001f, 0x000003e0, 0x00007c00, 0x00008000,),
           0x0b: (0x0000000f, 0x000000f0, 0x00000f00, 0x0000f000,)},
    0x20: {0x19: (0x3ff00000, 0x000ffc00, 0x000003ff, 0xc0000000,),
           0x1a: (0x000000ff, 0x0000ff00, 0x00ff0000, 0xff000000,)},
}


def main():
    #####################################################################################################
    ########################################### Parse options ###########################################

    filenames, output, gfd, surfMode, perfModulation, tileMode, swizzle, SRGB = processArgv()

    #####################################################################################################
    ############################################ PNG Reading ############################################

    if len(filenames) != 1:
        raise ValueError("Expected only one DDS file as input, but multiple files were given!")

    # Read the whole file
    with open(filenames.pop(0), "rb") as inf:
        inb = inf.read()

    # Create a new DDSHeader object
    header = DDSHeader()

    # Parse the input file, throw an exception if reading failed
    try:
        header.load(inb)

    except:
        raise RuntimeError("Not a valid DDS input file!") from None

    # Get misc. values
    width = header.width
    height = header.height
    numMips = header.mipMapCount

    # Make sure YUV is not being used
    if header.pixelFormat.flags & DDSHeader.PixelFormat.Flags.YUV.value:
        raise NotImplementedError("YUV color space is not supported!")

    # Treat uncompressed formats differently
    if not (header.pixelFormat.flags & DDSHeader.PixelFormat.Flags.FourCC.value):
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
        alphaOnly = header.pixelFormat.flags & DDSHeader.PixelFormat.Flags.Alpha.value
        hasAlpha = header.pixelFormat.flags & DDSHeader.PixelFormat.Flags.AlphaPixels.value
        RGB = header.pixelFormat.flags & DDSHeader.PixelFormat.Flags.RGB.value

        # Determine the optimal format and component selectors from the RGBA masks
        for format_, masks in validComps[bitsPerPixel].items():
            if alphaOnly:  # Alpha-only
                if aMask in masks:
                    compSel = (GX2CompSel.Component.One.value << 24 |
                               GX2CompSel.Component.One.value << 16 |
                               GX2CompSel.Component.One.value << 8  |
                               masks.index(aMask))
                    break

            elif hasAlpha and RGB:  # RGBA
                if rMask in masks and gMask in masks and bMask in masks and aMask in masks:
                    compSel = (masks.index(rMask) << 24 |
                               masks.index(gMask) << 16 |
                               masks.index(bMask) << 8  |
                               masks.index(aMask))
                    break

            elif hasAlpha:  # LA (Luminance + Alpha)
                if rMask in masks and aMask in masks:
                    compSel = (masks.index(rMask) << 24 |
                               masks.index(rMask) << 16 |
                               masks.index(rMask) << 8  |
                               masks.index(aMask))
                    break

            elif RGB:  # RGB
                if rMask in masks and gMask in masks and bMask in masks:
                    compSel = (masks.index(rMask) << 24 |
                               masks.index(gMask) << 16 |
                               masks.index(bMask) << 8  |
                               GX2CompSel.Component.One.value)
                    break

            else:  # Luminance
                if rMask in masks:
                    compSel = (masks.index(rMask) << 24 |
                               masks.index(rMask) << 16 |
                               masks.index(rMask) << 8  |
                               GX2CompSel.Component.One.value)
                    break

        else:
            raise RuntimeError("Could not determine the texture format of the input DDS file!")

        # If determined format is RGBA8, check and add SRGB mask
        if format_ == 0x1a and SRGB: format_ |= 0x400
        format_ = GX2SurfaceFormat(format_)

        # Calculate imageSize for this level
        imageSize = width * height * (bitsPerPixel >> 3)

    else:
        # DX10 is not supported yet
        if header.pixelFormat.fourCC == b'DX10':
            raise NotImplementedError("DX10 DDS files are not supported!")

        # Validate FourCC
        ## TODO: BC4 and BC5
        elif header.pixelFormat.fourCC not in fourCCs:
            raise RuntimeError("Unrecognized FourCC: %s" % repr(header.pixelFormat.fourCC))

        # DDS is incapable of letting you select the components for BCn
        compSel = GX2CompSel.RGBA

        # Determine the format and blockSize, check and add SRGB mask
        format_, blockSize = fourCCs[header.pixelFormat.fourCC]
        if SRGB: format_ |= 0x400
        format_ = GX2SurfaceFormat(format_)

        # Calculate imageSize for this level
        imageSize = ((width+3) >> 2) * ((height+3) >> 2) * blockSize

    # Get imageData and mipData
    imageData = inb[DDSHeader.size() : DDSHeader.size() + imageSize]
    mipData = inb[DDSHeader.size() + imageSize :]

    # Add the texture to the GFD file
    gfd.textures.append(Linear2DToGX2Texture(
        width, height, numMips, format_, compSel, imageData,
        tileMode, swizzle, mipData, surfMode, perfModulation,
    ))

    # Print debug info
    GX2TexturePrintInfo(gfd.textures[-1])

    with open(output, "wb+") as outf:
        outf.write(gfd.save())


if __name__ == '__main__':
    main()