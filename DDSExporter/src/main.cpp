#include <ninTexUtils/gfd/gfdStruct.h>

#include <filedevice/rio_FileDeviceMgr.h>

#include <filesystem>
#include <format>
#include <iostream>

static inline EndsWith(const std::string& s, const std::string& suffix)
{
    return s.size() >= suffix.size() && s.substr(s.size() - suffix.size()) == suffix;
}

int main(int argc, char* argv[])
{
    rio::FileDeviceMgr::createSingleton();

    int errorcode = 0;

    // Check input
    if (argc < 2)
    {
_invalid_input:
        std::cerr << "No valid input file was given!" << std::endl;
        errorcode = -1;
        goto _exit;
    }
    else
    {
        const std::string& file = argv[argc - 1];

        rio::NativeFileDevice* const device = rio::FileDeviceMgr::instance()->getNativeFileDevice();

        if (!device->isExistFile(file))
            goto _invalid_input;

        // Read the whole file
        rio::FileDevice::LoadArg arg;
        arg.path = file;
        u8* inb = device->load(arg);

        // Create a new GFDFile object & parse the input
        GFDFile gfd;
        size_t read_size = gfd.load(inb);
        assert(read_size <= arg.read_size);

        // Free file
        rio::MemUtil::free(inb);

        // Get the filename without the extension
        const std::filesystem::path& path_file = file;
        const std::string& ext = path_file.extension().string();
        assert(EndsWith(file, ext));
        const std::string& filename = file.substr(0, file.size() - ext.size());

        // Export any present textures
        if (gfd.mTextures.size() == 1)
        {
            size_t fileSize;
            u8* dds = GX2TextureToDDS(&(gfd.mTextures[0]), &fileSize);
            assert(dds);

            {
                rio::FileHandle handle;
                rio::FileDevice* ret = device->open(&handle, filename + ".dds", rio::FileDevice::FILE_OPEN_FLAG_CREATE);
                assert(ret && "Could not open output file for writing.");
                handle.write(dds, fileSize);
            }

            std::free(dds);
        }
        else
        {
            for (size_t i = 0, num = gfd.mTextures.size(); i < num; i++)
            {
                size_t fileSize;
                u8* dds = GX2TextureToDDS(&(gfd.mTextures[i]), &fileSize);
                assert(dds);

                {
                    rio::FileHandle handle;
                    rio::FileDevice* ret = device->open(&handle, filename + "_image" + std::to_string(i) + ".dds", rio::FileDevice::FILE_OPEN_FLAG_CREATE);
                    assert(ret && "Could not open output file for writing.");
                    handle.write(dds, fileSize);
                }

                std::free(dds);
            }
        }
    }

_exit:
    rio::FileDeviceMgr::destroySingleton();
    return errorcode;
}
