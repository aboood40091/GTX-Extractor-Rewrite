import enum


class GFDGPUVersion(enum.IntEnum):
    Zero = 0
    One  = 1
    GPU7 = 2


class GFDAlignMode(enum.IntEnum):
    Disable = 0
    Enable  = 1


class GFDBlockTypeV0(enum.IntEnum):
    # Basic
    Invalid     = 0
    End         = 1
    Pad         = 2
    Usr         = 16

    # Vertex Shader
    VSH_Header  = 3
    VSH_Program = 5

    # Pixel Shader
    PSH_Header  = 6
    PSH_Program = 7

    # Geometry Shader
    GSH_Header  = 8
    GSH_Program = 9

    #     version-0-specific values     #

    # GX2 Texture
    GX2Texture_Header    = 10
    GX2Texture_ImageData = 11
    GX2Texture_MipData   = 12

    # Geometry Shader (cont.)
    GSH_CopyProgram      = 13

    # Reserved
    Reserved_1           = 14
    Reserved_2           = 15


class GFDBlockTypeV1(enum.IntEnum):
    # Basic
    Invalid     = 0
    End         = 1
    Pad         = 2
    Usr         = 16

    # Vertex Shader
    VSH_Header  = 3
    VSH_Program = 5

    # Pixel Shader
    PSH_Header  = 6
    PSH_Program = 7

    # Geometry Shader
    GSH_Header  = 8
    GSH_Program = 9

    #   version-1-specific values   #

    # Geometry Shader (cont.)
    GSH_CopyProgram      = 10

    # GX2 Texture
    GX2Texture_Header    = 11
    GX2Texture_ImageData = 12
    GX2Texture_MipData   = 13

    # Compute Shader
    CSH_Header           = 14
    CSH_Program          = 15
