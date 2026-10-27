#pragma once

#include <cstddef>
#include <cstdlib>
#include <limits>
#include <new>
#include <type_traits>
#include <utility>

namespace lqcd_native {

// Internal host buffers only: no alignment requirement is added to the public
// ABI or to individual rows. Odd block sizes and SIMD tails remain supported.
template <class T> struct WorkspaceAllocator {
    using value_type = T;
    using size_type = std::size_t;
    using difference_type = std::ptrdiff_t;
    using is_always_equal = std::true_type;
    using propagate_on_container_move_assignment = std::true_type;

    template <class U> struct rebind {
        using other = WorkspaceAllocator<U>;
    };
    WorkspaceAllocator() noexcept = default;
    template <class U> WorkspaceAllocator(const WorkspaceAllocator<U> &) noexcept {}

    [[nodiscard]] T *allocate(size_type count) {
        if (count > max_size())
            throw std::bad_alloc();
        if (count == 0)
            return nullptr;
        void *storage = nullptr;
        constexpr size_type alignment = alignof(T) > 64 ? alignof(T) : 64;
        if (::posix_memalign(&storage, alignment, count * sizeof(T)) != 0)
            throw std::bad_alloc();
        return static_cast<T *>(storage);
    }
    void deallocate(T *storage, size_type) noexcept { std::free(storage); }
    constexpr size_type max_size() const noexcept {
        return std::numeric_limits<size_type>::max() / sizeof(T);
    }

    // Default-inserted scalar workspaces are overwritten by their owning
    // computation. Explicit fill/copy arguments must retain normal semantics.
    template <class U> void construct(U *p) { ::new (static_cast<void *>(p)) U; }
    template <class U, class A, class... Args> void construct(U *p, A &&a, Args &&...args) {
        ::new (static_cast<void *>(p)) U(std::forward<A>(a), std::forward<Args>(args)...);
    }
    template <class U> void destroy(U *p) { p->~U(); }
};

template <class T, class U>
bool operator==(const WorkspaceAllocator<T> &, const WorkspaceAllocator<U> &) noexcept {
    return true;
}
template <class T, class U>
bool operator!=(const WorkspaceAllocator<T> &, const WorkspaceAllocator<U> &) noexcept {
    return false;
}

} // namespace lqcd_native
