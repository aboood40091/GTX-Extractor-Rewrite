# Built-in libraries
import os
import sys

# Local libraries
from gfd import GFDFile
from png_export import GX2TextureToPNG


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
        pngs = GX2TextureToPNG(texture)
        for j, png in enumerate(pngs):
            png.save('%s_image%d_level%d.png' % (filename, i, j))


if __name__ == '__main__':
    main()
