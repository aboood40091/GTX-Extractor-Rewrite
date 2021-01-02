# Built-in libraries
import os
import sys

# Local libraries
from addrlib import surfaceGetBitsPerPixel as getBitsPerPixel
from dds import DDSHeader
from gfd import GFDFile
from gx2Texture import GX2TileMode, GX2Surface, GX2CompSel, GX2Texture, GX2TexturePrintInfo


fourCCs = {
    0x31: b'DXT1',
    0x32: b'DXT3',
    0x33: b'DXT5',
}

validComps = {
    0x01: (0x000000ff,),
    0x02: (0x0000000f, 0x000000f0,),
    0x07: (0x000000ff, 0x0000ff00,),
    0x08: (0x0000001f, 0x000007e0, 0x0000f800,),
    0x0a: (0x0000001f, 0x000003e0, 0x00007c00, 0x00008000,),
    0x0b: (0x0000000f, 0x000000f0, 0x00000f00, 0x0000f000,),
    0x19: (0x3ff00000, 0x000ffc00, 0x000003ff, 0xc0000000,),
    0x1a: (0x000000ff, 0x0000ff00, 0x00ff0000, 0xff000000,),
}


def GX2TextureToDDS(texture, printInfo=True):
    # Print debug info if specified
    if printInfo:
        GX2TexturePrintInfo(texture)

    # Check if format is supported
    if texture.surface.format.value not in (
        0x1, 0x2, 0x7, 0x8, 0xa,
        0xb, 0x19, 0x1a, 0x41a,
        0x31, 0x431, 0x32, 0x432,
        0x33, 0x433,
        # TODO: BC4 and BC5
    ):
        raise NotImplementedError("Unimplemented texture format: %s" % repr(texture.surface.format))

    # Check if the Component Selectors are supported
    r, g, b, a = GX2CompSel.getCompSelAsArray(texture.compSel)
    if 4 in (r, g, b, a):
        raise ValueError("Exporting as DDS with Component Selector set to Zero is not supported!")

    ## Check if One is used, but texture is not alpha-only
    if 5 in (r, g, b) and not (r == g == b and a < 4):
        raise ValueError("Exporting as DDS with RGB Component Selectors set to One and not alpha-only is not supported!")

    # Create a new GX2Texture to store the untiled texture
    linear_texture = GX2Texture.initTexture(
        texture.surface.dim, texture.surface.width, texture.surface.height,
        texture.surface.depth, texture.surface.numMips, texture.surface.format,
        texture.compSel, GX2TileMode.Linear_Special,
    )

    # Untile our texture
    GX2Surface.copySurface(texture.surface, linear_texture.surface)

    # Bits-per-pixel and bytes-per-pixel
    bitsPerPixel = getBitsPerPixel(texture.surface.format.value)
    bytesPerPixel = bitsPerPixel // 8

    # Create a new DDSHeader object
    header = DDSHeader()

    # Set misc. values
    header.width = texture.surface.width
    header.height = texture.surface.height
    header.caps |= DDSHeader.Caps.Texture.value

    # Set the mipmaps count and flags
    if texture.surface.numMips > 1:
        header.mipMapCount = texture.surface.numMips
        header.flags |= DDSHeader.Flags.MipMapCount.value
        header.caps |= (DDSHeader.Caps.Complex.value | DDSHeader.Caps.MipMap.value)

    # Treat uncompressed formats differently
    if not texture.surface.format.isCompressed():
        # Set the bits-per-pixel
        header.pixelFormat.rgbBitCount = bitsPerPixel

        # Set the pitch and its flag
        header.pitchOrLinearSize = header.width * bytesPerPixel
        header.flags |= DDSHeader.Flags.Pitch.value

        # Valid masks for this texture format
        masks = validComps[texture.surface.format.value & 0x3F]

        # Check alpha
        alphaOnly = False
        if a < 4:
            # Validate Alpha
            if not 0 <= a < len(masks):
                raise ValueError("Invalid Alpha channel Component Selector: %s" % repr(GX2CompSel.Component(a)))

            header.pixelFormat.aBitMask = masks[a]

            if r == g == b == 5:
                # Alpha-only (specifically A8, but could be anything)
                alphaOnly = True
                header.pixelFormat.flags |= DDSHeader.PixelFormat.Flags.Alpha.value

            else:
                # Has alpha
                header.pixelFormat.flags |= DDSHeader.PixelFormat.Flags.AlphaPixels.value

        else:  # a == 5
            # No alpha
            header.pixelFormat.aBitMask = 0

        # Handle colors if not alpha-only
        if not alphaOnly:
            # Check for RGB vs Luminance
            if r == g == b:
                # Luminance (specifically L8/LA4/LA8, but could be anything)
                header.pixelFormat.flags |= DDSHeader.PixelFormat.Flags.Luminance.value

            else:
                # Color
                header.pixelFormat.flags |= DDSHeader.PixelFormat.Flags.RGB.value

            # Validate Red
            if not 0 <= r < len(masks):
                raise ValueError("Invalid Red channel Component Selector: %s"   % repr(GX2CompSel.Component(r)))

            # Validate Green
            if not 0 <= g < len(masks):
                raise ValueError("Invalid Green channel Component Selector: %s" % repr(GX2CompSel.Component(g)))

            # Validate Blue
            if not 0 <= b < len(masks):
                raise ValueError("Invalid Blue channel Component Selector: %s"  % repr(GX2CompSel.Component(b)))

            # Set the RGB masks
            header.pixelFormat.rBitMask = masks[r]
            header.pixelFormat.gBitMask = masks[g]
            header.pixelFormat.bBitMask = masks[b]

    else:
        # Set fourCC and its flag
        header.pixelFormat.flags |= DDSHeader.PixelFormat.Flags.FourCC.value
        header.pixelFormat.fourCC = fourCCs[texture.surface.format.value & 0x3F]

        # Set the linear size and its flag
        header.pitchOrLinearSize = linear_texture.surface.imageSize
        header.flags |= DDSHeader.Flags.LinearSize.value

        # DDS is incapable of letting you select the components for BCn
        if texture.compSel != GX2CompSel.RGBA:
            raise ValueError("Exporting as compressed DDS with RGBA Component Selectors not set to RGBA is not supported!")

    return b''.join([header.save(), linear_texture.surface.imageData, linear_texture.surface.mipData])


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
    for i, texture in enumerate(gfd.textures):
        dds = GX2TextureToDDS(texture)
        with open('%s_image%d.dds' % (filename, i), "wb+") as outf:
            outf.write(dds)


if __name__ == '__main__':
    main()
