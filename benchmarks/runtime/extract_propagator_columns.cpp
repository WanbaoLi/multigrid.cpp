#include <algorithm>
#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

struct ComplexBytes { uint64_t real, imag; };
static_assert(sizeof(ComplexBytes) == 16);

int main(int argc, char **argv) {
    try {
        if (argc != 4) throw std::runtime_error("propagator.npy output_directory sites");
        const size_t sites = std::stoull(argv[3]);
        std::ifstream input(argv[1], std::ios::binary);
        std::array<unsigned char, 8> magic{};
        input.read(reinterpret_cast<char *>(magic.data()), magic.size());
        if (std::string(reinterpret_cast<char *>(magic.data()), 6) != "\x93NUMPY" ||
            magic[7] != 0 || (magic[6] != 1 && magic[6] != 2))
            throw std::runtime_error("unsupported NPY prefix");
        const int length_bytes = magic[6] == 1 ? 2 : 4;
        uint32_t header_length = 0;
        for (int i = 0; i < length_bytes; ++i) {
            int byte = input.get();
            if (byte < 0) throw std::runtime_error("truncated header");
            header_length |= uint32_t(byte) << (8 * i);
        }
        if (header_length > 65536) throw std::runtime_error("oversized header");
        std::string header(header_length, '\0');
        input.read(header.data(), header.size());
        if (header.find("'<c16'") == std::string::npos ||
            header.find("'fortran_order': False") == std::string::npos)
            throw std::runtime_error("expected C-order little-endian complex128");
        std::array<std::ofstream, 12> output;
        for (int col = 0; col < 12; ++col) {
            auto path = std::filesystem::path(argv[2]) / ("column" + std::to_string(col) + ".bin");
            if (std::filesystem::exists(path)) throw std::runtime_error("output already exists");
            output[col].open(path, std::ios::binary);
            if (!output[col]) throw std::runtime_error("cannot open column output");
        }
        constexpr size_t chunk_sites = 4096;
        std::vector<ComplexBytes> source(chunk_sites * 144), column(chunk_sites * 12);
        for (size_t begin = 0; begin < sites; begin += chunk_sites) {
            const size_t count = std::min(chunk_sites, sites - begin);
            const auto bytes = count * 144 * sizeof(ComplexBytes);
            input.read(reinterpret_cast<char *>(source.data()), bytes);
            if (size_t(input.gcount()) != bytes) throw std::runtime_error("truncated data");
            for (int col = 0; col < 12; ++col) {
                for (size_t site = 0; site < count; ++site)
                    for (int spin = 0; spin < 4; ++spin)
                        for (int color = 0; color < 3; ++color) {
                            const int component = ((spin * 4 + col / 3) * 3 + color) * 3 + col % 3;
                            column[site * 12 + spin * 3 + color] = source[site * 144 + component];
                        }
                output[col].write(reinterpret_cast<char *>(column.data()), count * 12 * sizeof(ComplexBytes));
                if (!output[col]) throw std::runtime_error("column write failed");
            }
        }
        if (input.get() != EOF) throw std::runtime_error("unexpected trailing bytes");
        std::cout << "Extracted 12 columns without arithmetic\n";
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
