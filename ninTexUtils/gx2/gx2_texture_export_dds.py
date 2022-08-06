from ..dds import DDSHeader

from .addrlib import surfaceGetBitsPerPixel as getBitsPerPixel

from .gx2Enum import GX2CompSel
from .gx2Enum import GX2TileMode

from .gx2Surface import GX2Surface

from .gx2Texture import GX2Texture
from .gx2Texture import GX2TexturePrintInfo


fourCCs = {
    0x031: b'DXT1',
    0x032: b'DXT3',
    0x033: b'DXT5',
    0x034: b'ATI1',
    0x035: b'ATI2',
    0x234: b'BC4S',
    0x235: b'BC5S',
}

validComps = {
    0x001: (0x000000ff,),
    0x002: (0x0000000f, 0x000000f0,),
    0x007: (0x000000ff, 0x0000ff00,),
    0x008: (0x0000001f, 0x000007e0, 0x0000f800,),
    0x00a: (0x0000001f, 0x000003e0, 0x00007c00, 0x00008000,),
    0x00b: (0x0000000f, 0x000000f0, 0x00000f00, 0x0000f000,),
    0x019: (0x3ff00000, 0x000ffc00, 0x000003ff, 0xc0000000,),
    0x01a: (0x000000ff, 0x0000ff00, 0x00ff0000, 0xff000000,),
}


def GX2TextureToDDS(texture, printInfo=True):
    # Print debug info if specified
    if printInfo:
        GX2TexturePrintInfo(texture)

    # Check if format is supported
    if texture.surface.format not in (
        0x001, 0x002, 0x007, 0x008, 0x00a,
        0x00b, 0x019, 0x01a, 0x41a,
        0x031, 0x431, 0x032, 0x432,
        0x033, 0x433, 0x034, 0x234,
        0x035, 0x235,
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

    # Bits-per-pixel and bytes-per-pixel
    bitsPerPixel = getBitsPerPixel(texture.surface.format)
    bytesPerPixel = bitsPerPixel // 8

    # Create a new DDSHeader object
    header = DDSHeader()

    # Set misc. values
    header.width = texture.surface.width
    header.height = texture.surface.height
    header.caps |= DDSHeader.Caps.Texture

    # Set the mipmaps count and flags
    if texture.surface.numMips > 1:
        header.mipMapCount = texture.surface.numMips
        header.flags |= DDSHeader.Flags.MipMapCount
        header.caps |= (DDSHeader.Caps.Complex | DDSHeader.Caps.MipMap)

    # Treat uncompressed formats differently
    if not texture.surface.format.isCompressed():
        # Set the bits-per-pixel
        header.pixelFormat.rgbBitCount = bitsPerPixel

        # Set the pitch and its flag
        header.pitchOrLinearSize = header.width * bytesPerPixel
        header.flags |= DDSHeader.Flags.Pitch

        # Check if the Component Selectors are supported
        r, g, b, a = GX2CompSel.getCompSelAsArray(texture.compSel)
        if 4 in (r, g, b, a):
            raise ValueError("Exporting as DDS with Component Selector set to Zero is not supported!")

        #   Check if One is used, but texture is not alpha-only
        if 5 in (r, g, b) and not (r == g == b and a < 4):
            raise ValueError("Exporting as DDS with RGB Component Selectors set to One and not alpha-only is not supported!")

        # Valid masks for this texture format
        masks = validComps[texture.surface.format & 0x3F]

        # Check alpha
        alphaOnly = False
        if a < 4:
            # Validate Alpha
            if not 0 <= a < len(masks):
                raise ValueError("Invalid Alpha Channel Component Selector: %s" % repr(GX2CompSel.Component(a)))

            header.pixelFormat.aBitMask = masks[a]

            if r == g == b == 5:
                # Alpha-only (specifically A8, but could be anything)
                alphaOnly = True
                header.pixelFormat.flags |= DDSHeader.PixelFormat.Flags.Alpha

            else:
                # Has alpha
                header.pixelFormat.flags |= DDSHeader.PixelFormat.Flags.AlphaPixels

        else:  # a == 5
            # No alpha
            header.pixelFormat.aBitMask = 0

        # Handle colors if not alpha-only
        if not alphaOnly:
            # Check for RGB vs Luminance
            if r == g == b:
                # Luminance (specifically L8/LA4/LA8, but could be anything)
                header.pixelFormat.flags |= DDSHeader.PixelFormat.Flags.Luminance

            else:
                # Color
                header.pixelFormat.flags |= DDSHeader.PixelFormat.Flags.RGB

            # Validate Red
            if not 0 <= r < len(masks):
                raise ValueError("Invalid Red Channel Component Selector: %s"   % repr(GX2CompSel.Component(r)))

            # Validate Green
            if not 0 <= g < len(masks):
                raise ValueError("Invalid Green Channel Component Selector: %s" % repr(GX2CompSel.Component(g)))

            # Validate Blue
            if not 0 <= b < len(masks):
                raise ValueError("Invalid Blue Channel Component Selector: %s"  % repr(GX2CompSel.Component(b)))

            # Set the RGB masks
            header.pixelFormat.rBitMask = masks[r]
            header.pixelFormat.gBitMask = masks[g]
            header.pixelFormat.bBitMask = masks[b]

    else:
        # Set fourCC and its flag
        header.pixelFormat.flags |= DDSHeader.PixelFormat.Flags.FourCC
        header.pixelFormat.fourCC = fourCCs[texture.surface.format & 0x3F + 0x200]

        # Set the linear size and its flag
        header.pitchOrLinearSize = linear_texture.surface.imageSize
        header.flags |= DDSHeader.Flags.LinearSize

        # DDS is incapable of letting you select the components for BCn
        if texture.surface.format & 4 or texture.compSel != GX2CompSel.RGBA:
            print("\nWarning: exporting as compressed DDS with application of RGBA Component Selectors is not possible!" \
                  "\nBe noted of the current RGBA Component Selectors when viewing the ouput DDS file or re-importing it." \
                  "\nIf you want to see what this texture really looks like, consider exporting as PNG instead.")

    return b''.join([header.save(), linear_texture.surface.imageData, linear_texture.surface.mipData])
