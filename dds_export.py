# Local libraries
from addrlib import surfaceGetBitsPerPixel as getBitsPerPixel
from dds import DDSHeader
from gx2Texture import GX2TileMode, GX2Surface, GX2CompSel, GX2Texture
from util import divRoundUp


fourCCs = {
    0x31: b'DXT1',
    0x32: b'DXT3',
    0x33: b'DXT5',
}

validComps = {
    0x1: {0: 0x000000ff},
    0x2: {0: 0x0000000f, 1: 0x000000f0},
    0x7: {0: 0x000000ff, 1: 0x0000ff00},
    0x8: {0: 0x0000001f, 1: 0x000007e0, 2: 0x0000f800},
    0xa: {0: 0x0000001f, 1: 0x000003e0, 2: 0x00007c00, 3: 0x00008000},
    0xb: {0: 0x0000000f, 1: 0x000000f0, 2: 0x00000f00, 3: 0x0000f000},
    0x19: {0: 0x3ff00000, 1: 0x000ffc00, 2: 0x000003ff, 3: 0xc0000000},
    0x1a: {0: 0x000000ff, 1: 0x0000ff00, 2: 0x00ff0000, 3: 0xff000000},
}


def GX2TextureToDDS(texture):
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

    if 5 in (r, g, b):
        raise ValueError("Exporting as DDS with RGB Component Selectors set to One is not supported!")

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
    bytesPerPixel = divRoundUp(bitsPerPixel, 8)

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
    if not texture.surface.format.isBC():
        # Set the pitch and its flag
        header.pitchOrLinearSize = header.width * bytesPerPixel
        header.flags |= DDSHeader.Flags.Pitch.value

        # Set the bits-per-pixel
        header.pixelFormat.rgbBitCount = bitsPerPixel

        # Check alpha
        alphaOnly = False
        if a < 4:
            if texture.surface.format.value == 0x1 and r in (0, 5) and g in (0, 5) and b in (0, 5) and a == 0:
                # Alpha-only (only A8 format for now)
                alphaOnly = True
                header.pixelFormat.flags |= DDSHeader.PixelFormat.Flags.Alpha.value

            else:
                # Has alpha
                header.pixelFormat.flags |= DDSHeader.PixelFormat.Flags.AlphaPixels.value

        # Valid components for this texture format
        formatValidComps = validComps[texture.surface.format.value & 0x3F]

        # Validate Alpha
        if 3 not in formatValidComps and a == 5:
            # Texture format doesn't have alpha
            header.pixelFormat.aBitMask = 0

        elif a not in formatValidComps:
            raise ValueError("Invalid Alpha channel Component Selector: %s" % repr(GX2CompSel.Component(a)))

        else:
            header.pixelFormat.aBitMask = formatValidComps[a]

        # Handle colors if not alpha-only
        if not alphaOnly:
            # Check for RGB vs Luminance
            if r == g == b and (texture.surface.format.value == 0x1 and r == 0
                                or texture.surface.format.value in (0x2, 0x7) and r in (0, 1)):
                # Luminance (specifically L8/LA4/LA8)
                header.pixelFormat.flags |= DDSHeader.PixelFormat.Flags.Luminance.value

            else:
                # Color
                header.pixelFormat.flags |= DDSHeader.PixelFormat.Flags.RGB.value

            # Validate Red
            if r not in formatValidComps:
                raise ValueError("Invalid Red channel Component Selector: %s" % repr(GX2CompSel.Component(r)))

            else:
                header.pixelFormat.rBitMask = formatValidComps[r]

            # Validate Green
            if g not in formatValidComps:
                raise ValueError("Invalid Green channel Component Selector: %s" % repr(GX2CompSel.Component(g)))

            else:
                header.pixelFormat.gBitMask = formatValidComps[g]

            # Validate Blue
            if b not in formatValidComps:
                raise ValueError("Invalid Blue channel Component Selector: %s" % repr(GX2CompSel.Component(b)))

            else:
                header.pixelFormat.bBitMask = formatValidComps[b]

    else:
        # Set the linear size and its flag
        header.pitchOrLinearSize = linear_texture.surface.imageSize
        header.flags |= DDSHeader.Flags.LinearSize.value

        # Set fourCC and its flag
        header.pixelFormat.flags |= DDSHeader.PixelFormat.Flags.FourCC.value
        header.pixelFormat.fourCC = fourCCs[texture.surface.format.value & 0x3F]

        ### TODO: Check components for BCn; DDS doesn't even let you pick ###

    return b''.join([header.save(), linear_texture.surface.imageData, linear_texture.surface.mipData])
