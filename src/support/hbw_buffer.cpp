#include "hbw_buffer.hpp"
#include <algorithm>
#include <cerrno>
#include <cstdlib>
#include <limits>
#include <new>
#include <utility>
#ifdef __linux__
#include <sys/syscall.h>
#include <unistd.h>
#endif
#if defined(LQCD_HAVE_KUPL)
#include <kupl.h>
#endif
namespace lqcd_native::hbm {
namespace {
bool valid_alignment(std::size_t n) {
    return n >= 64 && (n & (n - 1)) == 0;
}
} // namespace
Provider HbwBuffer::kupl_provider() noexcept {
#if defined(LQCD_HAVE_KUPL)
    return {kupl_hbw_malloc, kupl_hbw_free, kupl_hbw_verify};
#else
    return {};
#endif
}
HbwBuffer::HbwBuffer(std::size_t bytes, std::size_t alignment, Policy policy, std::size_t max_bytes,
                     Provider test_provider)
    : bytes_(bytes), alignment_(alignment) {
    if (!valid_alignment(alignment)) {
        error_ = "alignment must be a power of two";
        return;
    }
    if (max_bytes && bytes > max_bytes) {
        error_ = "HBW allocation exceeds configured limit";
        return;
    }
    if (!bytes)
        return;
    if (bytes > std::numeric_limits<std::size_t>::max() - (alignment - 1)) {
        error_ = "allocation size/alignment overflow";
        return;
    }
    Provider kupl =
        (test_provider.allocate || test_provider.deallocate) ? test_provider : kupl_provider();
    if (policy != Policy::Off) {
        const auto request = bytes + alignment - 1;
        if (max_bytes && request > max_bytes) {
            fallback_reason_ = "KUPL padded allocation exceeds limit";
        } else if (!kupl.allocate || !kupl.deallocate) {
            fallback_reason_ = "KUPL provider unavailable or incomplete";
        } else {
            raw_ = kupl.allocate(request);
            if (raw_) {
                const auto base = reinterpret_cast<std::uintptr_t>(raw_);
                if (base <= std::numeric_limits<std::uintptr_t>::max() - (alignment - 1)) {
                    data_ = reinterpret_cast<void *>((base + alignment - 1) & ~(alignment - 1));
                    provider_ = kupl;
                    backend_ = Backend::KUPL;
                    allocation_bytes_ = request;
                    return;
                }
                kupl.deallocate(raw_);
                raw_ = nullptr;
                fallback_reason_ = "KUPL pointer alignment overflow";
            } else
                fallback_reason_ = "KUPL allocation returned null";
        }
        if (policy == Policy::Require) {
            error_ = fallback_reason_;
            return;
        }
        fallback_ = true;
    }
    const int rc = ::posix_memalign(&raw_, alignment, bytes);
    if (rc != 0) {
        raw_ = nullptr;
        error_ = "posix_memalign failed: " + std::to_string(rc);
        return;
    }
    data_ = raw_;
    allocation_bytes_ = bytes;
    backend_ = Backend::PosixFallback;
}
void HbwBuffer::release() noexcept {
    if (!data_)
        return;
    if (backend_ == Backend::KUPL && provider_.deallocate)
        provider_.deallocate(raw_);
    else
        std::free(raw_ ? raw_ : data_);
    data_ = raw_ = nullptr;
    bytes_ = alignment_ = 0;
    backend_ = Backend::None;
}
HbwBuffer::~HbwBuffer() noexcept {
    release();
}
HbwBuffer::HbwBuffer(HbwBuffer &&o) noexcept {
    *this = std::move(o);
}
HbwBuffer &HbwBuffer::operator=(HbwBuffer &&o) noexcept {
    if (this != &o) {
        release();
        data_ = o.data_;
        raw_ = o.raw_;
        bytes_ = o.bytes_;
        alignment_ = o.alignment_;
        backend_ = o.backend_;
        provider_ = o.provider_;
        error_ = std::move(o.error_);
        fallback_reason_ = std::move(o.fallback_reason_);
        allocation_bytes_ = o.allocation_bytes_;
        fallback_ = o.fallback_;
        o.data_ = o.raw_ = nullptr;
        o.bytes_ = o.alignment_ = o.allocation_bytes_ = 0;
        o.backend_ = Backend::None;
        o.fallback_ = false;
    }
    return *this;
}
int HbwBuffer::verify_hbw() const {
    return backend_ == Backend::KUPL && data_ && provider_.verify
               ? provider_.verify(data_, bytes_, 0)
               : -2;
}
Sample HbwBuffer::sample_pages(std::size_t max_samples) const {
    Sample out;
#ifdef __linux__
#if defined(SYS_move_pages)
    if (!data_ || !bytes_ || !max_samples)
        return out;
    const long page = sysconf(_SC_PAGESIZE);
    if (page <= 0)
        return out;
    const auto base = reinterpret_cast<std::uintptr_t>(data_);
    const auto first_page = base - base % page;
    const std::size_t pages = 1 + ((base + bytes_ - 1) / page - first_page / page);
    const std::size_t count = std::min(pages, max_samples);
    std::vector<void *> addresses(count);
    out.nodes.assign(count, -1);
    for (std::size_t i = 0; i < count; i++)
        addresses[i] = reinterpret_cast<void *>(first_page + (i * (pages / count)) * page);
    errno = 0;
    out.query_rc =
        syscall(SYS_move_pages, 0, count, addresses.data(), nullptr, out.nodes.data(), 0);
    out.query_errno = out.query_rc < 0 ? errno : 0;
    out.pages = count;
    for (int n : out.nodes) {
        if (out.query_rc < 0 || n < 0)
            ++out.unknown;
        else
            ++out.known;
    }
#endif
#endif
    return out;
}
} // namespace lqcd_native::hbm
