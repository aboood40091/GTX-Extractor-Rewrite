import struct

from ...util import roundUp

from ..gx2Texture import GX2CompSel
from ..gx2Texture import GX2Texture

from .gfdEnum import GFDAlignMode
from .gfdEnum import GFDBlockTypeV0
from .gfdEnum import GFDBlockTypeV1
from .gfdEnum import GFDGPUVersion


class GFDHeader:
    _sFormat = '>4s5I8x'

    _magic = b'Gfx2'
    _size = struct.calcsize(_sFormat)
    _gpuVersion = GFDGPUVersion.GPU7

    def __init__(self, data=None, pos=0):
        self.majorVersion = 7
        self.minorVersion = 1
        self.alignMode = GFDAlignMode.Enable

        if data:
            self.load(data, pos)

    def load(self, data, pos=0):
        (magic,
         size,
         self.majorVersion,
         self.minorVersion,
         gpuVersion,
         alignMode) = struct.unpack_from(self._sFormat, data, pos)

        assert magic == self._magic
        assert size == self._size
        assert self.majorVersion in (6, 7)
        assert gpuVersion == self._gpuVersion

        self.alignMode = GFDAlignMode(alignMode)

    def save(self):
        return struct.pack(
            self._sFormat,
            self._magic,
            self._size,
            self.majorVersion,
            self.minorVersion,
            self._gpuVersion,
            self.alignMode,
        )

    @staticmethod
    def size():
        return 0x20


class GFDBlockHeader:
    _sFormat = '>4s5I8x'

    _magic = b'BLK{'
    _size = struct.calcsize(_sFormat)

    def __init__(self, data=None, pos=0):
        self.majorVersion = 1
        self.minorVersion = 0
        self.typeEnum = GFDBlockTypeV1
        self.type = self.typeEnum.Invalid
        self.dataSize = 0

        if data:
            self.load(data, pos)

    def setVersion(self, majorVersion, minorVersion):
        self.majorVersion, self.minorVersion = majorVersion, minorVersion
        self.typeEnum = GFDBlockTypeV1 if self.majorVersion == 1 else GFDBlockTypeV0

    def load(self, data, pos=0):
        (magic,
         size,
         majorVersion,
         minorVersion,
         type_,
         self.dataSize) = struct.unpack_from(self._sFormat, data, pos)

        assert magic == self._magic
        assert size == self._size
        assert majorVersion in (0, 1)

        self.setVersion(majorVersion, minorVersion)
        self.type = self.typeEnum(type_)

        assert self.type != self.typeEnum.Invalid
        if self.type == self.typeEnum.End:
            assert self.dataSize == 0

    def save(self):
        return struct.pack(
            self._sFormat,
            self._magic,
            self._size,
            self.majorVersion,
            self.minorVersion,
            self.type,
            self.dataSize,
        )

    @staticmethod
    def size():
        return 0x20


class GFDFile:
    def __init__(self):
        self.header = GFDHeader()
        self.textures = []

    def setVersion(self, majorVersion, minorVersion, perfModulation=None):
        assert majorVersion in (6, 7)
        self.header.majorVersion = majorVersion
        self.header.minorVersion = minorVersion

        surfMode = 1 if majorVersion == 6 else 0

        if perfModulation is None:
            perfModulation = 0 if majorVersion == 6 else 7

        for texture in self.textures:
            texture.initTextureRegs(surfMode, perfModulation)

        return surfMode, perfModulation

    def load(self, data, pos=0):
        start = pos

        self.header.load(data, pos)
        pos += GFDHeader.size()

        blocks = [
            [],  # GX2Texture_Header
            [],  # GX2Texture_ImageData
            [],  # GX2Texture_MipData
        ]

        blockHeaderSize = GFDBlockHeader.size()
        gx2TextureSize = GX2Texture.size()

        while True:
            blockHeader = GFDBlockHeader(data, pos)
            pos += blockHeaderSize

            if blockHeader.type == blockHeader.typeEnum.End:
                break

            elif blockHeader.type == blockHeader.typeEnum.GX2Texture_Header:
                assert blockHeader.dataSize == gx2TextureSize
                blocks[0].append(GX2Texture(data, pos))

            elif blockHeader.type == blockHeader.typeEnum.GX2Texture_ImageData:
                blocks[1].append(data[pos:pos + blockHeader.dataSize])

            elif blockHeader.type == blockHeader.typeEnum.GX2Texture_MipData:
                blocks[2].append(data[pos:pos + blockHeader.dataSize])

            pos += blockHeader.dataSize

        imageDataIdx = 0
        mipDataIdx = 0
        self.textures = []

        for texture in blocks[0]:
            imageData = blocks[1][imageDataIdx]
            imageDataIdx += 1

            texture.surface.imageData = imageData
            assert len(imageData) == texture.surface.imageSize

            if texture.surface.numMips > 1:
                mipData = blocks[2][mipDataIdx]
                mipDataIdx += 1

                texture.surface.mipData = mipData
                assert len(mipData) == texture.surface.mipSize

            self.textures.append(texture)

        return pos - start

    def save(self):
        # Determine the usual block header version from the file version
        blockMajorVersion, blockMinorVersion = (0, 1) if (self.header.majorVersion, self.header.minorVersion) == (6, 0) else (1, 0)

        # Check alignment
        align = self.header.alignMode == GFDAlignMode.Enable

        outBuffer = bytearray()
        pos = 0

        outBuffer += self.header.save()
        pos += GFDHeader.size()

        blockHeaderSize = GFDBlockHeader.size()
        gx2TextureSize = GX2Texture.size()

        blockHeader = GFDBlockHeader()
        blockHeader.setVersion(blockMajorVersion, blockMinorVersion)

        for texture in self.textures:
            # Write GX2Texture Header block
            blockHeader.type = blockHeader.typeEnum.GX2Texture_Header
            blockHeader.dataSize = gx2TextureSize

            outBuffer += blockHeader.save()
            pos += blockHeaderSize

            outBuffer += texture.save()
            pos += gx2TextureSize

            if align:
                # Write Pad block for the image data
                #   Calculate the needed pad
                dataPos = pos + blockHeaderSize * 2
                padSize = roundUp(dataPos, texture.surface.alignment) - dataPos

                blockHeader.type = blockHeader.typeEnum.Pad
                blockHeader.dataSize = padSize

                outBuffer += blockHeader.save()
                pos += blockHeaderSize

                outBuffer += b'\0' * padSize
                pos += padSize

            blockHeader.type = blockHeader.typeEnum.GX2Texture_ImageData
            blockHeader.dataSize = texture.surface.imageSize

            outBuffer += blockHeader.save()
            pos += blockHeaderSize

            outBuffer += texture.surface.imageData
            pos += texture.surface.imageSize

            if texture.surface.mipData:
                if align:
                    # Write Pad block for the mipmap data
                    #   Calculate the needed pad
                    dataPos = pos + blockHeaderSize * 2
                    padSize = roundUp(dataPos, texture.surface.alignment) - dataPos

                    blockHeader.type = blockHeader.typeEnum.Pad
                    blockHeader.dataSize = padSize

                    outBuffer += blockHeader.save()
                    pos += blockHeaderSize

                    outBuffer += b'\0' * padSize
                    pos += padSize

                blockHeader.type = blockHeader.typeEnum.GX2Texture_MipData
                blockHeader.dataSize = texture.surface.mipSize

                outBuffer += blockHeader.save()
                pos += blockHeaderSize

                outBuffer += texture.surface.mipData
                pos += texture.surface.mipSize

        blockHeader.type = blockHeader.typeEnum.End
        blockHeader.dataSize = 0

        outBuffer += blockHeader.save()
        pos += blockHeaderSize

        assert len(outBuffer) == pos
        return outBuffer
