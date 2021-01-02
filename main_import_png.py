# Local libraries
from gx2Enum import GX2SurfaceFormat, GX2CompSel
from gx2Texture import GX2TexturePrintInfo, Linear2DToGX2Texture
from importOptions import processArgv

# pypng
from png import Reader as png_reader


def main():
    #####################################################################################################
    ########################################### Parse options ###########################################

    filenames, output, gfd, surfMode, perfModulation, tileMode, swizzle, SRGB = processArgv()

    #####################################################################################################
    ############################################ PNG Reading ############################################

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

    # Add the texture to the GFD file
    gfd.textures.append(Linear2DToGX2Texture(
        baseWidth, baseHeight, 1+len(filenames),
        GX2SurfaceFormat.SRGB_RGBA8 if SRGB else GX2SurfaceFormat.Unorm_RGBA8,  # TODO: RGBA8, for now
        GX2CompSel.RGBA, imageData, tileMode, swizzle, mipData,
        surfMode, perfModulation,
    ))

    # Print debug info
    GX2TexturePrintInfo(gfd.textures[-1])

    with open(output, "wb+") as outf:
        outf.write(gfd.save())


if __name__ == '__main__':
    main()
