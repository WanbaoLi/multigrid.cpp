#pragma once
#include "../../support/aligned_workspace.hpp"
#include <algorithm>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <vector>

namespace lqcd_native::detail {

// Owned spinor entries remain private. Unowned halo pages are scratch for only
// the current synchronous operator. Different active RHS use different files.
// Only used with the large mmap-backed WorkspaceAllocator reservations.
class FineHaloStorage {
    struct Region { size_t first, bytes, file_offset; };
    std::vector<Region> regions_;
    std::vector<int> files_;
    size_t total_elements_, page_bytes_, slot_bytes_ = 0;

  public:
    FineHaloStorage(size_t first, size_t end, size_t face, size_t total)
        : total_elements_(total), page_bytes_(0) {
        const long page=sysconf(_SC_PAGESIZE);
        if (page>0) page_bytes_=size_t(page);
        if (!page_bytes_ || !face || first >= end || end > total ||
            face > end-first || total > std::numeric_limits<size_t>::max()/sizeof(float))
            throw std::runtime_error("invalid reusable fine halo geometry");
        const size_t starts[2] = {(first + total - face) % total, end % total};
        for (size_t start : starts) {
            if (start + face > total || (start < end && start + face > first))
                throw std::runtime_error("fine halo would overlap owned values");
            // Never replace a partial page shared with owned entries.
            const size_t begin = (start*sizeof(float)+page_bytes_-1)/page_bytes_*page_bytes_;
            const size_t finish = (start+face)*sizeof(float)/page_bytes_*page_bytes_;
            if (finish <= begin ||
                std::any_of(regions_.begin(),regions_.end(),[&](const Region &r){return r.first==begin;}))
                continue;
            regions_.push_back({begin, finish-begin, slot_bytes_});
            slot_bytes_ += finish-begin;
        }
    }
    ~FineHaloStorage() { for (int fd : files_) close(fd); }
    FineHaloStorage(const FineHaloStorage &) = delete;
    FineHaloStorage &operator=(const FineHaloStorage &) = delete;
    size_t page_bytes() const { return page_bytes_; }
    size_t bytes_per_slot() const { return slot_bytes_; }
    size_t slots() const { return files_.size(); }

    template<class Field> bool bind(const Field &field, int slot) {
        if (field.size()!=total_elements_ || slot<0 || slot>=12)
            throw std::runtime_error("invalid reusable fine halo field/slot");
        if (!slot_bytes_ || field.size()*sizeof(float) < WorkspaceAllocator<float>::minimum_mmap_bytes)
            return false; // posix_memalign allocations must never be MAP_FIXED.
        auto *base = reinterpret_cast<char *>(const_cast<float *>(field.data()));
        if (reinterpret_cast<std::uintptr_t>(base)%page_bytes_)
            throw std::runtime_error("large fine workspace is not a page-aligned mapping");
        while (files_.size()<=size_t(slot)) {
#ifdef SYS_memfd_create
            // MFD_CLOEXEC = 1; syscall avoids requiring a newer libc wrapper.
            const int fd = int(syscall(SYS_memfd_create,"lqcd-fine-halo",1u));
#else
            const int fd = -1;
#endif
            if (fd<0) throw std::runtime_error("cannot create reusable fine halo memfd");
            if (ftruncate(fd,off_t(slot_bytes_))) {
                close(fd);
                throw std::runtime_error("cannot size reusable fine halo memfd");
            }
            files_.push_back(fd);
        }
        // Rebind every application. A vector allocator may have reused a
        // previous address; a pointer-only mapping cache would be invalid.
        for (const auto &r : regions_) {
            void *address = base+r.first;
            if (mmap(address,r.bytes,PROT_READ|PROT_WRITE,MAP_SHARED|MAP_FIXED,
                     files_[slot],off_t(r.file_offset)) != address)
                throw std::runtime_error("cannot bind reusable fine halo pages");
        }
        return true;
    }
};
}
