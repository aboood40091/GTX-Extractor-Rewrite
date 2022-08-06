# Built-in libraries
import os
import sys

# Local libraries
from ninTexUtils.gx2.gfd import GFDFile
from ninTexUtils.gx2 import GX2TextureToDDS


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
        dds = GX2TextureToDDS(gfd.textures[0])
        with open('%s.dds' % filename, "wb+") as outf:
            outf.write(dds)

    else:
        for i, texture in enumerate(gfd.textures):
            dds = GX2TextureToDDS(texture)
            with open('%s_image%d.dds' % (filename, i), "wb+") as outf:
                outf.write(dds)


if __name__ == '__main__':
    main()
