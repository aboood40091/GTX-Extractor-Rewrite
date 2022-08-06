# Local libraries
from ninTexUtils.gx2 import GX2TexturePrintInfo
from ninTexUtils.gx2 import DDSToGX2Texture, PNGToGX2Texture
from import_options import processArgv


def main():
    # Parse options
    filenames, output, gfd, surfMode, perfModulation, tileMode, swizzle, SRGB, compSelIdx = processArgv()

    # DDS Reading
    if filenames[0][-4:] == ".dds":
        if len(filenames) != 1:
            raise ValueError("Expected only one DDS file as input, but multiple files were given!")

        texture = DDSToGX2Texture(filenames.pop(0), surfMode, perfModulation, tileMode, swizzle, SRGB, compSelIdx)

    # PNG Reading
    else:
        texture = PNGToGX2Texture(filenames, surfMode, perfModulation, tileMode, swizzle, SRGB, compSelIdx)

    # GTX Writing
    #   Add the texture to the GFD file
    gfd.textures.append(texture)

    with open(output, "wb+") as outf:
        outf.write(gfd.save())


if __name__ == '__main__':
    main()
