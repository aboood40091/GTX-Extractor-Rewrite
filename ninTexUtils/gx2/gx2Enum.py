import enum


class GX2SurfaceDim(enum.IntEnum):
    Dim1D            = 0
    Dim2D            = 1
    Dim3D            = 2
    DimCube          = 3
    Dim1D_Array      = 4
    Dim2D_Array      = 5
    Dim2D_MSAA       = 6
    Dim2D_MSAA_Array = 7


class GX2SurfaceFormat(enum.IntEnum):
    Invalid       = 0x000
    Unorm_RG4     = 0x002
    Unorm_RGBA4   = 0x00b
    Unorm_R8      = 0x001
    Unorm_RG8     = 0x007
    Unorm_RGBA8   = 0x01a
    Unorm_R16     = 0x005
    Unorm_RG16    = 0x00f
    Unorm_RGBA16  = 0x01f
    Unorm_RGB565  = 0x008
    Unorm_RGB5A1  = 0x00a
    Unorm_A1BGR5  = 0x00c
    Unorm_R24X8   = 0x011
    Unorm_A2BGR10 = 0x01b
    Unorm_RGB10A2 = 0x019
    Unorm_BC1     = 0x031
    Unorm_BC2     = 0x032
    Unorm_BC3     = 0x033
    Unorm_BC4     = 0x034
    Unorm_BC5     = 0x035
    Unorm_NV12    = 0x081

    Uint_R8       = 0x101
    Uint_RG8      = 0x107
    Uint_RGBA8    = 0x11a
    Uint_R16      = 0x105
    Uint_RG16     = 0x10f
    Uint_RGBA16   = 0x11f
    Uint_R32      = 0x10d
    Uint_RG32     = 0x11d
    Uint_RGBA32   = 0x122
    Uint_A2BGR10  = 0x11b
    Uint_RGB10A2  = 0x119
    Uint_X24G8    = 0x111
    Uint_G8X24    = 0x11c

    Snorm_R8      = 0x201
    Snorm_RG8     = 0x207
    Snorm_RGBA8   = 0x21a
    Snorm_R16     = 0x205
    Snorm_RG16    = 0x20f
    Snorm_RGBA16  = 0x21f
    Snorm_RGB10A2 = 0x219
    Snorm_BC4     = 0x234
    Snorm_BC5     = 0x235

    Sint_R8       = 0x301
    Sint_RG8      = 0x307
    Sint_RGBA8    = 0x31a
    Sint_R16      = 0x305
    Sint_RG16     = 0x30f
    Sint_RGBA16   = 0x31f
    Sint_R32      = 0x30d
    Sint_RG32     = 0x31d
    Sint_RGBA32   = 0x322
    Sint_RGB10A2  = 0x319

    SRGB_RGBA8    = 0x41a
    SRGB_BC1      = 0x431
    SRGB_BC2      = 0x432
    SRGB_BC3      = 0x433

    Float_R32     = 0x80e
    Float_RG32    = 0x81e
    Float_RGBA32  = 0x823
    Float_R16     = 0x806
    Float_RG16    = 0x810
    Float_RGBA16  = 0x820
    Float_RG11B10 = 0x816
    Float_D24S8   = 0x811
    Float_X8X24   = 0x81c

    def isCompressed(self):
        return 0x31 <= (self & 0x3f) <= 0x35


class GX2AAMode(enum.IntEnum):
    Mode1X = 0
    Mode2X = 1
    Mode4X = 2
    Mode8X = 3


class GX2SurfaceUse(enum.IntFlag):
    Texture     = 0x00000001
    ColorBuffer = 0x00000002
    DepthBuffer = 0x00000004
    ScanBuffer  = 0x00000008
    TV          = 0x80000000

    ColorBuffer_Texture    = Texture | ColorBuffer
    DepthBuffer_Texture    = Texture | DepthBuffer
    ColorBuffer_Texture_TV = Texture | ColorBuffer | TV
    ColorBuffer_TV         = ColorBuffer | TV


class GX2TileMode(enum.IntEnum):
    Default        = 0
    Linear_Aligned = 1
    Tiled_1D_Thin1 = 2
    Tiled_1D_Thick = 3
    Tiled_2D_Thin1 = 4
    Tiled_2D_Thin2 = 5
    Tiled_2D_Thin4 = 6
    Tiled_2D_Thick = 7
    Tiled_2B_Thin1 = 8
    Tiled_2B_Thin2 = 9
    Tiled_2B_Thin4 = 10
    Tiled_2B_Thick = 11
    Tiled_3D_Thin1 = 12
    Tiled_3D_Thick = 13
    Tiled_3B_Thin1 = 14
    Tiled_3B_Thick = 15
    Linear_Special = 16


class GX2CompSel:
    # Predefined compSels
    ZZZO = 0x04040405
    RZZO = 0x00040405
    RGZO = 0x00010405
    RGBO = 0x00010205
    RGBA = 0x00010203
    RRRR = 0x00000000
    GGGG = 0x01010101
    BBBB = 0x02020202
    AAAA = 0x03030303
    ABGR = 0x03020100
    ARGB = 0x03000102

    class Component(enum.IntEnum):
        Red = 0
        Green = 1
        Blue = 2
        Alpha = 3
        Zero = 4
        One = 5

    @staticmethod
    def getComponent(compSel, i):
        return GX2CompSel.Component((compSel >> (24 - 8 * i)) & 0xFF)

    @staticmethod
    def getComp0(compSel):
        return GX2CompSel.getComponent(compSel, 0)

    @staticmethod
    def getComp1(compSel):
        return GX2CompSel.getComponent(compSel, 1)

    @staticmethod
    def getComp2(compSel):
        return GX2CompSel.getComponent(compSel, 2)

    @staticmethod
    def getComp3(compSel):
        return GX2CompSel.getComponent(compSel, 3)

    @staticmethod
    def getCompSel(comp0, comp1, comp2, comp3):
        return (comp0 & 0xFF) << 24 |  \
               (comp1 & 0xFF) << 16 |  \
               (comp2 & 0xFF) << 8  |  \
               (comp3 & 0xFF)

    @staticmethod
    def getCompSelAsArray(compSel):
        return [(compSel >> (24 - 8 * i)) & 0xFF for i in range(4)]
