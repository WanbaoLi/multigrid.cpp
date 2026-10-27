#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace lqcd_native::hbm {
enum class Policy { Off, Prefer, Require };
enum class Backend { None, KUPL, PosixFallback };
struct Provider {
    void *(*allocate)(std::size_t) = nullptr;
    void (*deallocate)(void *) = nullptr;
    int (*verify)(void *, std::size_t, int) = nullptr;
};
struct Sample {
    long query_rc = 0;
    int query_errno = 0;
    std::size_t pages = 0, known = 0, unknown = 0;
    std::vector<int> nodes;
};
// Off uses ordinary aligned host allocation (no KUPL call). Prefer falls back
// on provider failure; Require fails rather than using ordinary allocation.
// max_bytes=0 means no limit; a nonzero limit includes KUPL alignment padding.
// No memory is touched/initialized. KUPL success is provenance, NOT HBM proof.
// An empty/error/moved-from buffer converts to false; inspect error() for failure.
// Provider callbacks must not throw and must remain loaded until destruction.
class HbwBuffer {
  public:
    HbwBuffer() noexcept = default;
    HbwBuffer(std::size_t bytes, std::size_t alignment = 64, Policy policy = Policy::Off,
              std::size_t max_bytes = 0, Provider test_provider = {});
    ~HbwBuffer() noexcept;
    HbwBuffer(const HbwBuffer &) = delete;
    HbwBuffer &operator=(const HbwBuffer &) = delete;
    HbwBuffer(HbwBuffer &&other) noexcept;
    HbwBuffer &operator=(HbwBuffer &&other) noexcept;
    void *data() noexcept { return data_; }
    const void *data() const noexcept { return data_; }
    std::size_t size() const noexcept { return bytes_; }
    std::size_t alignment() const noexcept { return alignment_; }
    Backend backend() const noexcept { return backend_; }
    bool fallback() const noexcept { return fallback_; }
    std::size_t allocation_bytes() const noexcept { return allocation_bytes_; }
    const std::string &fallback_reason() const noexcept { return fallback_reason_; }
    const std::string &error() const noexcept { return error_; }
    explicit operator bool() const noexcept { return data_ != nullptr; }
    Sample sample_pages(std::size_t max_samples = 64) const;
    // Does not touch pages: SDK flags=0. -2 means unavailable/not KUPL;
    // SDK returns 1=HBW, 0=not HBW, -1=query error. No MPI or allocation.
    int verify_hbw() const;
    static Provider kupl_provider() noexcept;

  private:
    void *data_ = nullptr, *raw_ = nullptr;
    std::size_t bytes_ = 0, alignment_ = 0;
    Backend backend_ = Backend::None;
    Provider provider_{};
    std::string error_, fallback_reason_;
    std::size_t allocation_bytes_ = 0;
    bool fallback_ = false;
    void release() noexcept;
};
} // namespace lqcd_native::hbm
