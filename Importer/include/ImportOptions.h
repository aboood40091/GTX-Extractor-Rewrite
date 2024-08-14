#pragma once

#include <misc/rio_Types.h>

#include <ninTexUtils/gfd/gfdStruct.h>

#include <string>
#include <vector>

enum ImportError
{
    IMPORT_ERROR_OK = 0,
    IMPORT_ERROR_NO_INPUT,
    IMPORT_ERROR_APPEND_NO_INPUT,
    IMPORT_ERROR_INPUT_NOT_EXIST,
    IMPORT_ERROR_NO_OUTPUT,
    IMPORT_ERROR_APPEND_OUTPUT_NOT_EXIST,
    IMPORT_ERROR_INPUT_INVALID_EXT,
    IMPORT_ERROR_MULTI_VERSION,
    IMPORT_ERROR_NO_TILE_MODE,
    IMPORT_ERROR_INVALID_TILE_MODE,
    IMPORT_ERROR_NO_SWIZZLE,
    IMPORT_ERROR_INVALID_SWIZZLE,
    IMPORT_ERROR_NO_COMP_SEL,
    IMPORT_ERROR_INVALID_COMP_SEL,
    IMPORT_ERROR_MULTI_DDS,                 // Not handled in processArgv()
    IMPORT_ERROR_HELP,
};

struct ImportOptions
{
    std::vector<std::string>    filenames;
    std::string                 output;
    GFDFile                     gfd;
    u8                          swizzle;
    bool                        SRGB;
    GX2TileMode                 tileMode;
    u32                         compSel;

    ImportOptions()
    {
    }

    ~ImportOptions()
    {
    }
};

void printHelp();
ImportError processArgv(ImportOptions* p_options, const std::vector<std::string>& arg);
