# Built-in libraries
import os
import sys

# Local libraries
from ninTexUtils.gx2.gfd import GFDFile, GFDAlignMode
from ninTexUtils.gx2 import GX2TileMode


def print_help():
    # TODO
    pass


def processArgv():
    argv = sys.argv
    argc = len(argv)

    if argc < 2:
        raise ValueError("No valid input file was given! Use command (--help) for help.")

    # Available options
    option_help     = '--help'
    option_input    = '-i'
    option_output   = '-o'
    option_append   = '-a'
    option_noalign  = '-no-align'
    option_v6       = '-v6'
    option_v6_1     = '-v6_1'
    option_v7       = '-v7'
    option_tileMode = '-tileMode'
    option_swizzle  = '-swizzle'
    option_SRGB     = '-SRGB'
    option_compSel  = '-compSel'

    # Tuple of all available options
    options = (
        option_help, option_input, option_output, option_append,
        option_noalign, option_v6, option_v6_1, option_v7,
        option_tileMode, option_swizzle, option_SRGB, option_compSel,
    )
    # Tuple of verion options
    options_version = (option_v6, option_v6_1, option_v7)

    # Print the instructions if the help option is used and terminate program
    if option_help in argv:
        return print_help()

    # If the append option is enabled, check if the input was specified
    if option_append in argv and not option_input in argv:
        raise ValueError("Append option (-a) cannot be enabled without specifying the inputs using (-i)!")

    # Handle specifying the input
    if option_input in argv:
        # Read input list
        start = argv.index(option_input) + 1
        end = start
        for _ in range(start, argc):
            if argv[end] in options:
                break

            end += 1

        filenames = argv[start:end]

    else:
        # Single input
        name = argv[-1]
        if name in options:
            raise ValueError("No valid input file was given!")

        filenames = [name]

    # Check if all inputs exist
    for name in filenames:
        if not os.path.isfile(name):
            raise RuntimeError("Could not locate the input file: %s" % name)

    # Handle specifying the output
    if option_output in argv:
        idx = argv.index(option_output) + 1
        if idx == argc:
            raise ValueError("(-o) was specified, but no valid filename was given!")

        output = argv[idx]
        if output in options:
            raise ValueError("(-o) was specified, but no valid filename was given!")

    # Output not specified, but append option is enabled
    elif option_append in argv:
        output = filenames[0]
        if not os.path.isfile(output):
            raise RuntimeError("Could not locate the output file: %s" % output)

    # Get ouput name from first input name
    else:
        name, ext = os.path.splitext(filenames[0])
        if ext in (".png", ".dds"):
            if name[-14:] == "_image0_level0":
                name = name[:-14]

            elif name[-7:] == "_image0":
                name = name[:-7]

            elif name[-7:] == "_level0":
                name = name[:-7]

        else:
            raise ValueError("Expected input file to end with \".png\" or \".dds\"")


        output = name + ".gtx"

    # Create a new GFDFile object
    gfd = GFDFile()

    # Handle append option
    if option_append in argv:
        # Read the whole file
        with open(filenames.pop(0), "rb") as inf:
            inb = inf.read()

        # Parse the input GFD file, throw an exception if reading failed
        try:
            gfd.load(inb)

        except:
            raise RuntimeError("Not a valid GFD input file!") from None

    # If "no align" option enabled, disable aligning data
    gfd.header.alignMode = GFDAlignMode.Disable if option_noalign in argv else GFDAlignMode.Enable

    # Handle the case of specifying multiple version options
    if sum(option in argv for option in options_version) > 1:
        raise ValueError("Cannot specify multiple version options!")

    # Version 6.0
    if option_v6 in argv:
        majorVersion, minorVersion = 6, 0

    # Version 6.1
    elif option_v6_1 in argv:
        majorVersion, minorVersion = 6, 1

    # Version 7.1 (default)
    else:  # option_v7 in argv
        majorVersion, minorVersion = 7, 1

    # Set the version and get the corresponding "surfMode" and "perfModulation"
    surfMode, perfModulation = gfd.setVersion(majorVersion, minorVersion)

    # Handle specifying the tileMode
    if option_tileMode in argv:
        idx = argv.index(option_tileMode) + 1
        if idx == argc:
            raise ValueError("(-tileMode) was specified, but no valid tileMode was entered!")

        try:
            tileMode = int(argv[idx], 0)
        except ValueError:
            raise ValueError("(-tileMode) was specified, but no valid tileMode was entered!") from None

        if tileMode < GX2TileMode.Default.value or tileMode > GX2TileMode.Linear_Special.value:
            raise ValueError("Invalid tileMode value entered! Expected value between 0 and 16.")

        tileMode = GX2TileMode(tileMode)

    else:
        tileMode = GX2TileMode.Default

    # Handle specifying the swizzle
    if option_swizzle in argv:
        idx = argv.index(option_swizzle) + 1
        if idx == argc:
            raise ValueError("(-swizzle) was specified, but no valid swizzle value was entered!")

        try:
            swizzle = int(argv[idx], 0)
        except ValueError:
            raise ValueError("(-swizzle) was specified, but no valid swizzle value was entered!") from None

        if swizzle < 0 or swizzle > 7:
            raise ValueError("Invalid swizzle value entered! Expected value between 0 and 7.")
    else:
        swizzle = 0

    # Use SRGB when possible
    SRGB = option_SRGB in argv

    # Handle specifying the compSel
    if option_compSel in argv:
        idx = argv.index(option_compSel) + 1
        if idx == argc:
            raise ValueError("(-compSel) was specified, but no valid compSel value was entered!")

        compSelStr = argv[idx].upper()
        if len(compSelStr) != 4 or not all(comp in 'RGBA01' for comp in compSelStr):
            raise ValueError("Invalid compSel value entered! Expected 4-character combination of the characters \"R, G, B, A, 0 and 1\".")

        compSel = tuple('RGBA01'.index(comp) for comp in compSelStr)

    else:
        compSel = (0, 1, 2, 3)

    return filenames, output, gfd, surfMode, perfModulation, tileMode, swizzle, SRGB, compSel
