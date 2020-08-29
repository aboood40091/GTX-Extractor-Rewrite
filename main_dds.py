# Built-in libraries
import os
import sys

# Local libraries
from gfd import GFDFile
from dds_export import GX2TextureToDDS


def main():
    # Check input
    file = sys.argv[-1]
    if not os.path.isfile(file):
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
        raise RuntimeError("Not a valid input file!") from None

    # Get the filename without the extension
    filename = os.path.splitext(file)[0]

    # Export any present textures
    for i, texture in enumerate(gfd.textures):
        dds = GX2TextureToDDS(texture)
        with open('%s_image%d.dds' % (filename, i), "wb+") as outf:
            outf.write(dds)


if __name__ == '__main__':
    main()
