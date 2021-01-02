# Built-in libraries
import os
import sys

# Local libraries
import bcn
from gfd import GFDFile
from gx2Texture import GX2TileMode, GX2Surface, GX2CompSel, GX2Texture, GX2TexturePrintInfo

try:
    import pyximport
    pyximport.install()

    import gx2FormConv_cy as formConv

except ImportError:
    import gx2FormConv as formConv

# pypng
from png import from_array as png_from_array


# Supported formats
formats = {
    0x1: ('l8', 1),
    0x2: ('la4', 1),
    0x7: ('la8', 2),
    0x8: ('rgb565', 2),
    0xa: ('rgb5a1', 2),
    0xb: ('rgba4', 2),
    0x19: ('bgr10a2', 4),
    0x1a: ('rgba8', 4),
    0x31: ('rgba8', 4),
    0x32: ('rgba8', 4),
    0x33: ('rgba8', 4),
    0x34: ('rgba8', 4),
    0x35:  ('rgba8', 4),
}

def texureToRGBA8(width, height, format_, data, compSel):
    formatStr, bpp = formats[format_ & 0x3F]

    ### Decompress the data if compressed ###

    if (format_ & 0x3F) == 0x31:
        data = bcn.decompressDXT1(data, width, height)

    elif (format_ & 0x3F) == 0x32:
        data = bcn.decompressDXT3(data, width, height)

    elif (format_ & 0x3F) == 0x33:
        data = bcn.decompressDXT5(data, width, height)

    elif (format_ & 0x3F) == 0x34:
        data = bcn.decompressBC4(data, width, height, format_ >> 8)

    elif (format_ & 0x3F) == 0x35:
        data = bcn.decompressBC5(data, width, height, format_ >> 8)

    return formConv.torgba8(width, height, bytearray(data), formatStr, bpp, compSel)


def GX2SurfaceGetLevels(surface):
    levels = []
    levels.append(surface.imageData[:surface.imageSize])

    for mipLevel in range(1, surface.numMips):
        if mipLevel == 1:
            offset = 0
        else:
            offset = surface.mipOffset[mipLevel - 1]

        end = surface.mipOffset[mipLevel] if mipLevel < surface.numMips - 1 else surface.mipSize
        levels.append(surface.mipData[offset:end])

    return levels


def GX2TextureToPNG(texture, printInfo=True):
    # Print debug info if specified
    if printInfo:
        GX2TexturePrintInfo(texture)

    # Check if format is supported
    if texture.surface.format.value not in (
        0x1, 0x2, 0x7, 0x8, 0xa,
        0xb, 0x19, 0x1a, 0x41a,
        0x31, 0x431, 0x32, 0x432,
        0x33, 0x433, 0x34, 0x234,
        0x35, 0x235,
    ):
        raise NotImplementedError("Unimplemented texture format: %s" % repr(texture.surface.format))

    # Create a new GX2Texture to store the untiled texture
    linear_texture = GX2Texture.initTexture(
        texture.surface.dim, texture.surface.width, texture.surface.height,
        texture.surface.depth, texture.surface.numMips, texture.surface.format,
        texture.compSel, GX2TileMode.Linear_Special,
    )

    # Untile our texture
    GX2Surface.copySurface(texture.surface, linear_texture.surface)

    levels = GX2SurfaceGetLevels(linear_texture.surface)
    for i, data in enumerate(levels):
        # Calculate the width and height of the level
        width = max(1, texture.surface.width >> i)
        height = max(1, texture.surface.height >> i)

        # Process the data into RGBA8 data
        result = texureToRGBA8(
            width, height, texture.surface.format.value,
            data, GX2CompSel.getCompSelAsArray(texture.compSel),
        )

        # Create an array that satisfies png.from_array
        pixels = tuple(result[y * width * 4 : (y+1) * width * 4] for y in range(height))
        yield png_from_array(pixels, 'RGBA')


def main():
    # Check input
    file = sys.argv[-1]
    if len(sys.argv) < 2 or not os.path.isfile(file):
        raise RuntimeError("No valid input file was given!")

    # Read the whole file
    with open(file, "rb") as inf:
        inb = inf.read()

    # Create a new GFDFile object
    gfd = GFDFile()

    # Parse the input file, throw an exception if reading failed
    try:
        gfd.load(inb)

    except:
        raise RuntimeError("Not a valid GFD input file!") from None

    # Get the filename without the extension
    filename = os.path.splitext(file)[0]

    # Export any present textures
    if len(gfd.textures) == 1:
        texture = gfd.textures[0]
        if texture.surface.numMips == 1:
            next(GX2TextureToPNG(texture)).save('%s.png' % filename)

        else:
            for j, png in enumerate(GX2TextureToPNG(texture)):
                png.save('%s_level%d.png' % (filename, j))

    else:
        for i, texture in enumerate(gfd.textures):
            if texture.surface.numMips == 1:
                next(GX2TextureToPNG(texture)).save('%s_image%d.png' % (filename, i))

            else:
                for j, png in enumerate(GX2TextureToPNG(texture)):
                    png.save('%s_image%d_level%d.png' % (filename, i, j))


if __name__ == '__main__':
    main()
