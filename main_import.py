# Local libraries
from dds import DDSHeader
from gx2Enum import GX2SurfaceFormat, GX2CompSel
from gx2Texture import GX2TexturePrintInfo, Linear2DToGX2Texture
from importOptions import processArgv

# pypng
from png import Reader as png_reader


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

    filenames, output, gfd, surfMode, perfModulation, tileMode, swizzle, SRGB, compSelIdx = processArgv()

    #####################################################################################################
    ############################################ DDS Reading ############################################

    if filenames[0][-4:] == ".dds":
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

        if header.depth > 1 or header.caps2 & DDSHeader.Caps2.Volume.value:
            raise NotImplementedError("3D textures are not supported!")

        if header.caps2 & (DDSHeader.Caps2.CubeMap.value
                           | DDSHeader.Caps2.CubeMap_PositiveX.value
                           | DDSHeader.Caps2.CubeMap_NegativeX.value
                           | DDSHeader.Caps2.CubeMap_PositiveY.value
                           | DDSHeader.Caps2.CubeMap_NegativeY.value
                           | DDSHeader.Caps2.CubeMap_PositiveZ.value
                           | DDSHeader.Caps2.CubeMap_NegativeZ.value):
            raise NotImplementedError("Cube Maps are not supported!")

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
                        compSelArr = (GX2CompSel.Component.One.value,
                                      GX2CompSel.Component.One.value,
                                      GX2CompSel.Component.One.value,
                                      masks.index(aMask),
                                      GX2CompSel.Component.Zero.value,
                                      GX2CompSel.Component.One.value)
                        break

                elif hasAlpha and RGB:  # RGBA
                    if rMask in masks and gMask in masks and bMask in masks and aMask in masks:
                        compSelArr = (masks.index(rMask),
                                      masks.index(gMask),
                                      masks.index(bMask),
                                      masks.index(aMask),
                                      GX2CompSel.Component.Zero.value,
                                      GX2CompSel.Component.One.value)
                        break

                elif hasAlpha:  # LA (Luminance + Alpha)
                    if rMask in masks and aMask in masks:
                        compSelArr = (masks.index(rMask),
                                      masks.index(rMask),
                                      masks.index(rMask),
                                      masks.index(aMask),
                                      GX2CompSel.Component.Zero.value,
                                      GX2CompSel.Component.One.value)
                        break

                elif RGB:  # RGB
                    if rMask in masks and gMask in masks and bMask in masks:
                        compSelArr = (masks.index(rMask),
                                      masks.index(gMask),
                                      masks.index(bMask),
                                      GX2CompSel.Component.One.value,
                                      GX2CompSel.Component.Zero.value,
                                      GX2CompSel.Component.One.value)
                        break

                else:  # Luminance
                    if rMask in masks:
                        compSelArr = (masks.index(rMask),
                                      masks.index(rMask),
                                      masks.index(rMask),
                                      GX2CompSel.Component.One.value,
                                      GX2CompSel.Component.Zero.value,
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
            compSelArr = (GX2CompSel.Component.Red.value,
                          GX2CompSel.Component.Green.value,
                          GX2CompSel.Component.Blue.value,
                          GX2CompSel.Component.Alpha.value,
                          GX2CompSel.Component.Zero.value,
                          GX2CompSel.Component.One.value)

            # Determine the format and blockSize, check and add SRGB mask
            format_, blockSize = fourCCs[header.pixelFormat.fourCC]
            if SRGB: format_ |= 0x400
            format_ = GX2SurfaceFormat(format_)

            # Calculate imageSize for this level
            imageSize = ((width+3) >> 2) * ((height+3) >> 2) * blockSize

        # Get imageData and mipData
        imageData = inb[DDSHeader.size() : DDSHeader.size() + imageSize]
        mipData = inb[DDSHeader.size() + imageSize :]

    #####################################################################################################
    ############################################ PNG Reading ############################################

    else:
        # Read the base image (level 0)
        reader = png_reader(filename=filenames.pop(0))
        baseWidth, baseHeight, rows, info = reader.asRGBA8(); del reader

        imageData = bytearray(pixel for row in rows for pixel in row)
        mipData = bytearray()

        # Read the remaining levels
        for i, name in enumerate(filenames):
            # Don't allow more than 13 mipmaps
            mipLevel = i + 1
            if mipLevel > 13:
                break

            reader = png_reader(filename=name)
            width, height, rows, info = reader.asRGBA8(); del reader

            # Make sure they are in order and the correct size
            assert width == max(1, baseWidth >> mipLevel)
            assert height == max(1, baseHeight >> mipLevel)

            mipData += bytearray(pixel for row in rows for pixel in row)

        width = baseWidth
        height = baseHeight
        numMips = 1+len(filenames)

        # TODO: RGBA8, for now
        format_ = GX2SurfaceFormat.SRGB_RGBA8 if SRGB else GX2SurfaceFormat.Unorm_RGBA8
        compSelArr = (GX2CompSel.Component.Red.value,
                      GX2CompSel.Component.Green.value,
                      GX2CompSel.Component.Blue.value,
                      GX2CompSel.Component.Alpha.value,
                      GX2CompSel.Component.Zero.value,
                      GX2CompSel.Component.One.value)

    #####################################################################################################
    ############################################ GTX Writing ############################################

    # Combine the component selectors read from the input files and the user
    compSel = (compSelArr[compSelIdx[0]] << 24 |
               compSelArr[compSelIdx[1]] << 16 |
               compSelArr[compSelIdx[2]] << 8  |
               compSelArr[compSelIdx[3]])

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
