#include <ImportOptions.h>

#include <filedevice/rio_FileDeviceMgr.h>

#include <algorithm>
#include <array>
#include <charconv>
#include <filesystem>

// Available options
static const std::string option_help     = "--help";
static const std::string option_input    = "-i";
static const std::string option_output   = "-o";
static const std::string option_append   = "-a";
static const std::string option_noalign  = "-no-align";
static const std::string option_v6       = "-v6";
static const std::string option_v6_1     = "-v6_1";
static const std::string option_v7       = "-v7";
static const std::string option_tileMode = "-tileMode";
static const std::string option_swizzle  = "-swizzle";
static const std::string option_SRGB     = "-SRGB";
static const std::string option_compSel  = "-compSel";

// Array of all available options
static const std::array<std::string, 12> options {
    option_help, option_input, option_output, option_append,
    option_noalign, option_v6, option_v6_1, option_v7,
    option_tileMode, option_swizzle, option_SRGB, option_compSel
};
// Array of verion options
static const std::array<std::string, 3> options_version {
    option_v6, option_v6_1, option_v7
};

template <typename T, typename U>
inline bool contains(const T& container, const U& value)
{
    return std::find(container.begin(), container.end(), value) != container.end();
}

void printHelp()
{
    // TODO
}

ImportError processArgv(ImportOptions* p_options, const std::vector<std::string>& arg)
{
#define HAS_ARG(option)     contains(arg, option)
#define FIND_ARG(option)    std::find(arg.begin(), arg.end(), option)
#define ARG_FOUND(it)       (it != arg.end())
#define IS_OPTION(str)      contains(options, str)

    RIO_ASSERT(p_options != nullptr);

    if (arg.size() < 2)
        return IMPORT_ERROR_NO_INPUT;

    // Print the instructions if the help option is used and terminate program
    if (HAS_ARG(option_help))
        return IMPORT_ERROR_HELP;

    // If the append option is enabled, check if the input was specified
    if (HAS_ARG(option_append) && !HAS_ARG(option_input))
        return IMPORT_ERROR_APPEND_NO_INPUT;

    auto& filenames = p_options->filenames;

    // Handle specifying the input
    const auto& it_input = FIND_ARG(option_input);
    if (ARG_FOUND(it_input))
    {
        // Read input list
        auto start = it_input + 1;
        auto end = start;
        while (end != arg.end())
        {
            if (IS_OPTION(*end))
                break;
            end++;
        }
        filenames.assign(start, end);
    }
    else
    {
        // Single input
        const std::string& name = arg.back();
        if (IS_OPTION(name))
            return IMPORT_ERROR_NO_INPUT;
        filenames.assign({ name });
    }

    rio::NativeFileDevice* p_device = rio::FileDeviceMgr::instance()->getNativeFileDevice();

    // Check if all inputs exist
    for (const auto& name : filenames)
        if (!p_device->isExistFile(name))
            return IMPORT_ERROR_INPUT_NOT_EXIST;

    auto& output = p_options->output;

    // Handle specifying the output
    const auto& it_output = FIND_ARG(option_output);
    if (ARG_FOUND(it_output))
    {
        auto idx = it_output + 1;
        if (idx == arg.end() || IS_OPTION(*idx))
            return IMPORT_ERROR_NO_OUTPUT;

        output = *idx;
    }
    // Output not specified, but append option is enabled
    else if (HAS_ARG(option_append))
    {
        if (!p_device->isExistFile(filenames[0]))
            return IMPORT_ERROR_APPEND_OUTPUT_NOT_EXIST;

        output = filenames[0];
    }
    // Get output name from first input name
    else
    {
        const std::filesystem::path first_input = filenames[0];
        std::string name = first_input.stem().string();
        const std::string& ext = first_input.extension().string();
        if (ext == ".png" || ext == ".dds")
        {
            if (name.size() >= 14 && name.substr(name.size()-14) == "_image0_level0")
                name = name.substr(0, name.size()-14);

            else if (name.size() >= 7 && name.substr(name.size()-7) == "_image0")
                name = name.substr(0, name.size()-7);

            else if (name.size() >= 7 && name.substr(name.size()-7) == "_level0")
                name = name.substr(0, name.size()-7);
        }
        else
        {
            return IMPORT_ERROR_INPUT_INVALID_EXT;
        }
        output = name + ".gtx";
    }

    GFDFile& gfd = p_options->gfd;

    // Handle append option
    if (HAS_ARG(option_append))
    {
        // Read the whole file
        rio::FileDevice::LoadArg arg;
        arg.path = filenames.front();
        filenames.erase(filenames.begin());
        u8* inb = p_device->load(arg);
        {
            // Parse the input GFD file
            gfd.load(inb);
        }
        rio::MemUtil::free(inb);
    }
    else
    {
        // Re-initialize GFDFile object
        gfd.destroy();
    }

    // If "no align" option enabled, disable aligning data
    // (TODO: V6 uses "undef")
    gfd.mHeader.alignMode = HAS_ARG(option_noalign) ? GFD_ALIGN_MODE_DISABLE : GFD_ALIGN_MODE_ENABLE;

    bool v6 = HAS_ARG(option_v6);
    bool v6_1 = HAS_ARG(option_v6_1);
    bool v7 = HAS_ARG(option_v7);

    if (((int)v6 + (int)v6_1 + (int)v7) > 1)
        return IMPORT_ERROR_MULTI_VERSION;

    // Version 6.0
    if (v6)
        gfd.setVersion(6, 0);
    // Version 6.1
    else if (v6_1)
        gfd.setVersion(6, 1);
    // Version 7.1 (default)
    else // if (v7)
        gfd.setVersion(7, 1);

    auto& tileMode = p_options->tileMode;

    // Handle specifying the tileMode
    const auto& it_tileMode = FIND_ARG(option_tileMode);
    if (ARG_FOUND(it_tileMode))
    {
        auto idx = it_tileMode + 1;
        if (idx == arg.end())
            return IMPORT_ERROR_NO_TILE_MODE;

        u32 tileMode_u;
        const auto& res = std::from_chars(idx->c_str(), idx->c_str() + idx->size(), tileMode_u);
        if (res.ec == std::errc::invalid_argument || !(GX2_TILE_MODE_DEFAULT <= tileMode_u && tileMode_u <= GX2_TILE_MODE_LINEAR_SPECIAL))
            return IMPORT_ERROR_INVALID_TILE_MODE;

        tileMode = GX2TileMode(tileMode_u);
    }
    else
    {
        tileMode = GX2_TILE_MODE_DEFAULT;
    }

    auto& swizzle = p_options->swizzle;

    // Handle specifying the swizzle
    const auto& it_swizzle = FIND_ARG(option_swizzle);
    if (ARG_FOUND(it_swizzle))
    {
        auto idx = it_swizzle + 1;
        if (idx == arg.end())
            return IMPORT_ERROR_NO_SWIZZLE;

        u32 swizzle_u;
        const auto& res = std::from_chars(idx->c_str(), idx->c_str() + idx->size(), swizzle_u);
        if (res.ec == std::errc::invalid_argument || !(0 <= swizzle_u && swizzle_u <= 7))
            return IMPORT_ERROR_INVALID_SWIZZLE;

        swizzle = swizzle_u;
    }
    else
    {
        swizzle = 0;
    }

    // Use SRGB when possible
    p_options->SRGB = HAS_ARG(option_compSel);

    auto& compSel = p_options->compSel;

    // Handle specifying the compSel
    const auto& it_compSel = FIND_ARG(option_compSel);
    if (ARG_FOUND(it_compSel))
    {
        auto idx = it_compSel + 1;
        if (idx == arg.end())
            return IMPORT_ERROR_NO_COMP_SEL;

        const std::string& compSel_s = *idx;
        if (compSel_s.size() != 4)
            return IMPORT_ERROR_INVALID_COMP_SEL;

        u32 compSel_u = 0;

        for (u32 i = 0; i < 4; i++)
        {
            switch (compSel_s[i])
            {
            default:
                return IMPORT_ERROR_INVALID_COMP_SEL;
            case 'r':
            case 'R':
                compSel_u |= 0 << (8 * (4 - (1 + i)));
                break;
            case 'g':
            case 'G':
                compSel_u |= 1 << (8 * (4 - (1 + i)));
                break;
            case 'b':
            case 'B':
                compSel_u |= 2 << (8 * (4 - (1 + i)));
                break;
            case 'a':
            case 'A':
                compSel_u |= 3 << (8 * (4 - (1 + i)));
                break;
            case '0':
                compSel_u |= 4 << (8 * (4 - (1 + i)));
                break;
            case '1':
                compSel_u |= 5 << (8 * (4 - (1 + i)));
                break;
            }
        }

        compSel = compSel_u;
    }
    else
    {
        compSel = 0x00010203;
    }

    return IMPORT_ERROR_OK;

#undef HAS_ARG
#undef FIND_ARG
#undef ARG_FOUND
}
