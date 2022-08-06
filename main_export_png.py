# Built-in libraries
import os
import sys

# Local libraries
from ninTexUtils.gx2.gfd import GFDFile
from ninTexUtils.gx2 import GX2TextureToPNG


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
