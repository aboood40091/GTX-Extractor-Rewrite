import enum
import struct


class DDSHeader:
    _sFormat = '<4s7I44x%dx2I12x' % DDSHeader.PixelFormat.size()

    _magic = b'DDS '
    _size = struct.calcsize(_sFormat) - 4

    class Flags(enum.Enum):
        Caps        = 0x1
        Height      = 0x2
        Width       = 0x4
        Pitch       = 0x8
        PixelFormat = 0x1000
        MipMapCount = 0x20000
        LinearSize  = 0x80000
        Depth       = 0x800000

    class PixelFormat:
        _sFormat = '<2I4s5I'
        _size = struct.calcsize(_sFormat)

        class Flags(enum.Enum):
            AlphaPixels = 0x1
            Alpha       = 0x2
            FourCC      = 0x4
            RGB         = 0x40
            YUV         = 0x200
            Luminance   = 0x20000

        def __init__(self, data=None, pos=0):
            self.flags = 0
            self.fourCC = b'\0\0\0\0'
            self.rgbBitCount = 0
            self.rBitMask = 0
            self.gBitMask = 0
            self.bBitMask = 0
            self.aBitMask = 0

            if data:
                self.load(data, pos)

        def load(self, data, pos=0):
            (size,
             self.flags,
             self.fourCC,
             self.rgbBitCount,
             self.rBitMask,
             self.gBitMask,
             self.bBitMask,
             self.aBitMask) = struct.unpack_from(self._sFormat, data, pos)

            assert size == self._size

            if self.flags & DDSHeader.PixelFormat.Flags.FourCC.value:
                assert self.fourCC != b'\0\0\0\0'

        def save(self):
            return struct.pack(
                self._sFormat,
                self._size,
                self.flags,
                self.fourCC,
                self.rgbBitCount,
                self.rBitMask,
                self.gBitMask,
                self.bBitMask,
                self.aBitMask,
            )

        @staticmethod
        def size():
            return 0x20

    class Caps(enum.Enum):
        Complex = 0x8
        Texture = 0x1000
        MipMap  = 0x400000

    class Caps2(enum.Enum):
        CubeMap           = 0x200
        CubeMap_PositiveX = 0x400
        CubeMap_NegativeX = 0x800
        CubeMap_PositiveY = 0x1000
        CubeMap_NegativeY = 0x2000
        CubeMap_PositiveZ = 0x4000
        CubeMap_NegativeZ = 0x8000
        Volume            = 0x200000

    def __init__(self, data=None, pos=0):
        self.flags = (DDSHeader.Flags.Caps.value  | DDSHeader.Flags.Height.value |
                      DDSHeader.Flags.Width.value | DDSHeader.Flags.PixelFormat.value)
        self.height = 0
        self.width = 0
        self.pitchOrLinearSize = 0
        self.depth = 0
        self.mipMapCount = 1
        self.pixelFormat = DDSHeader.PixelFormat()
        self.caps = 0
        self.caps2 = 0

        if data:
            self.load(data, pos)

    def load(self, data, pos=0):
        (magic,
         size,
         self.flags,
         self.height,
         self.width,
         self.pitchOrLinearSize,
         self.depth,
         self.mipMapCount,
         self.caps,
         self.caps2) = struct.unpack_from(self._sFormat, data, pos)

        self.pixelFormat.load(data, pos + 0x4c)

        assert magic == self._magic
        assert size == self._size

        assert self.flags & (DDSHeader.Flags.Caps.value  | DDSHeader.Flags.Height.value |
                             DDSHeader.Flags.Width.value | DDSHeader.Flags.PixelFormat.value)
        assert (self.flags & (DDSHeader.Flags.Pitch.value | DDSHeader.Flags.LinearSize.value)
                != (DDSHeader.Flags.Pitch.value | DDSHeader.Flags.LinearSize.value))  # Make sure they are not set together
        assert self.height != 0
        assert self.width != 0
        assert self.caps & DDSHeader.Caps.Texture.value

        if self.flags & (DDSHeader.Flags.Pitch.value | DDSHeader.Flags.LinearSize.value):
            assert self.pitchOrLinearSize != 0

        else:
            self.pitchOrLinearSize = 0

        if self.flags & DDSHeader.Flags.Depth.value:
            assert self.depth != 0

        else:
            self.depth = 0

        if self.flags & DDSHeader.Flags.MipMapCount.value:
            assert 1 <= self.mipMapCount <= 14

        else:
            self.mipMapCount = 1

    def save(self):
        pixelFormat = self.pixelFormat.save()
        header = bytearray(struct.pack(
            self._sFormat,
            self._magic,
            self._size,
            self.flags,
            self.height,
            self.width,
            self.pitchOrLinearSize,
            self.depth,
            self.mipMapCount,
            self.caps,
            self.caps2,
        ))

        header[0x4c:0x4c + DDSHeader.PixelFormat.size()] = pixelFormat

        return bytes(header)

    @staticmethod
    def size():
        return 0x80
