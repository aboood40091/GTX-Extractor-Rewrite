#include <ImportOptions.h>

#include <filedevice/rio_FileDeviceMgr.h>

#include <iostream>

int main(int argc, char* argv[])
{
    rio::FileDeviceMgr::createSingleton();

    int exitcode = 0;

    std::vector<std::string> arg;
    arg.reserve(argc);
    for (s32 i = 0; i < argc; i++)
        arg.emplace_back(argv[i]);

    // Parse options
    ImportOptions options;
    ImportError error = processArgv(&options, arg);
    switch (error)
    {
    case IMPORT_ERROR_OK:
        break;
    case IMPORT_ERROR_NO_INPUT:
        std::cout << "No valid input file was given! Use command (--help) for help." << std::endl;
        goto _exit_error;
    case IMPORT_ERROR_APPEND_NO_INPUT:
        std::cout << "Append option (-a) cannot be enabled without specifying the inputs using (-i)!" << std::endl;
        goto _exit_error;
    case IMPORT_ERROR_INPUT_NOT_EXIST:
        std::cout << "Could not locate one or more of the input files!" << std::endl;
        goto _exit_error;
    case IMPORT_ERROR_NO_OUTPUT:
        std::cout << "(-o) was specified, but no valid filename was given!" << std::endl;
        goto _exit_error;
    case IMPORT_ERROR_APPEND_OUTPUT_NOT_EXIST:
        std::cout << "Could not locate the output file for appending!" << std::endl;
        goto _exit_error;
    case IMPORT_ERROR_INPUT_INVALID_EXT:
        std::cout << "Expected input file to end with \".png\" or \".dds\"!" << std::endl;
        goto _exit_error;
    case IMPORT_ERROR_MULTI_VERSION:
        std::cout << "Cannot specify multiple version options!" << std::endl;
        goto _exit_error;
    case IMPORT_ERROR_NO_TILE_MODE:
        std::cout << "(-tileMode) was specified, but no valid tileMode was entered!" << std::endl;
        goto _exit_error;
    case IMPORT_ERROR_INVALID_TILE_MODE:
        std::cout << "Invalid tileMode value entered! Expected value between 0 and 16." << std::endl;
        goto _exit_error;
    case IMPORT_ERROR_NO_SWIZZLE:
        std::cout << "(-swizzle) was specified, but no valid swizzle value was entered!" << std::endl;
        goto _exit_error;
    case IMPORT_ERROR_INVALID_SWIZZLE:
        std::cout << "Invalid swizzle value entered! Expected value between 0 and 7." << std::endl;
        goto _exit_error;
    case IMPORT_ERROR_NO_COMP_SEL:
        std::cout << "(-compSel) was specified, but no valid compSel value was entered!" << std::endl;
        goto _exit_error;
    case IMPORT_ERROR_INVALID_COMP_SEL:
        std::cout << "Invalid compSel value entered! Expected 4-character combination of the characters \"R, G, B, A, 0 and 1\"." << std::endl;
        goto _exit_error;
    case IMPORT_ERROR_HELP:
        printHelp();
    default:
        goto _exit;
    }

    // On successful parsing of options
    {
        GFDFile& gfd = options.gfd;
        GX2Texture texture;

        rio::NativeFileDevice* const device = rio::FileDeviceMgr::instance()->getNativeFileDevice();

        const std::string& first_input = options.filenames[0];
        if (first_input.size() >= 4 && first_input.substr(first_input.size()-4) == ".dds")
        {
            if (options.filenames.size() > 1)
            {
                std::cout << "Expected only one DDS file as input, but multiple files were given!" << std::endl;
                error = IMPORT_ERROR_MULTI_DDS;
                goto _exit_error;
            }

            rio::FileDevice::LoadArg arg;
            arg.path = first_input;
            u8* inb = device->load(arg);
            GX2TextureFromDDS(&texture, inb, arg.read_size, options.tileMode, options.swizzle, options.SRGB, options.compSel, gfd.mHeader.majorVersion == 7);
            rio::MemUtil::free(inb);
        }
        else
        {
            for (const std::string& fname : options.filenames)
            {
                assert(fname.size() >= 4 && fname.substr(fname.size()-4) == ".png");
            }

            // TODO: PNG to GX2Texture
            assert(false && "PNG is not yet supported");
        }

        gfd.mTextures.push_back(texture);
        const std::vector<u8>& gfd_data = gfd.saveGTX();

        {
            rio::FileHandle handle;
            rio::FileDevice* ret = device->open(&handle, options.output, rio::FileDevice::FILE_OPEN_FLAG_CREATE);
            assert(ret && "Could not open output file for writing.");
            handle.write(gfd_data.data(), gfd_data.size());
        }

        free(texture.surface.imagePtr);
        texture.surface.imagePtr = nullptr;
        if (texture.surface.mipPtr)
        {
            free(texture.surface.mipPtr);
            texture.surface.mipPtr = nullptr;
        }
    }

_exit:
    rio::FileDeviceMgr::destroySingleton();
    return exitcode;

_exit_error:
    exitcode = (int)error;
    goto _exit;
}
