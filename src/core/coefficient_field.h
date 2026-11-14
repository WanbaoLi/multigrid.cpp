#pragma once
#include "core/field.h"
#include <algorithm>
#include <memory>
#include <stdexcept>
#include <string>
#include <sys/mman.h>
#include <unistd.h>

// Coefficients can own ordinary storage or view a collectively managed window.
// Spinors remain independent std::vectors. This class never makes MPI calls.
class CoefficientField {
    Field owned;
    bool chiral = false;
    Complex structural_zero{};
    Complex *shared = nullptr;
    size_t shared_count = 0;
    std::shared_ptr<void> owner;

  public:
    using value_type = Complex;
    CoefficientField() = default;
    CoefficientField(const CoefficientField &other)
        : owned(other.shared ? Field{} : Field(other.begin(), other.end())), shared(other.shared),
          shared_count(other.shared_count), owner(other.owner), chiral(other.chiral) {}
    CoefficientField &operator=(const CoefficientField &other) {
        if (this != &other) {
            chiral = other.chiral;
            if (other.shared) {
                owned.clear();
                shared = other.shared;
                shared_count = other.shared_count;
                owner = other.owner;
            } else {
                shared = nullptr;
                shared_count = 0;
                owner.reset();
                resize(other.size());
                std::copy(other.begin(), other.end(), begin());
            }
        }
        return *this;
    }
    void bind_shared(Complex *pointer, size_t count, std::shared_ptr<void> lifetime) {
        if (!pointer || !count || !owned.empty() || shared)
            throw std::runtime_error("coefficient shared storage must be bound once before use");
        shared = pointer;
        shared_count = count;
        owner = std::move(lifetime);
    }
    // Preserve global indices without physically replicating untouched ranks.
    // Only the caller's owned slab and explicit received halos are written.
    void reserve_sparse(size_t count, bool compact_chiral = false) {
        chiral = compact_chiral;
        const size_t bytes = (chiral ? count/2 : count) * sizeof(Complex);
        void *p = mmap(nullptr, bytes, PROT_READ | PROT_WRITE,
                       MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE, -1, 0);
        if (p == MAP_FAILED)
            throw std::bad_alloc();
        bind_shared(static_cast<Complex *>(p), count,
                    std::shared_ptr<void>(p, [bytes](void *q) { munmap(q, bytes); }));
    }
    bool is_shared() const { return shared != nullptr; }
    void discard_sparse_region(size_t first, size_t end) {
        if (!shared || first >= end) return;
        const size_t scale = chiral ? 2 : 1;
        const size_t page = (size_t)sysconf(_SC_PAGESIZE);
        size_t start = (first/scale*sizeof(Complex)+page-1)/page*page;
        size_t last = end/scale*sizeof(Complex)/page*page;
        if (last>start && madvise(reinterpret_cast<char*>(shared)+start,last-start,MADV_DONTNEED))
            throw std::runtime_error("cannot release sparse coefficient halos");
    }
    void release_storage() {
        Field().swap(owned);
        shared = nullptr; shared_count = 0; owner.reset();
    }
    size_t size() const { return shared ? shared_count : owned.size(); }
    bool empty() const { return size() == 0; }
    Complex *data() { return shared ? shared : owned.data(); }
    const Complex *data() const { return shared ? shared : owned.data(); }
    Complex *begin() { if(chiral) throw std::runtime_error("no bulk iteration of compact basis"); return data(); }
    const Complex *begin() const { if(chiral) throw std::runtime_error("no bulk iteration of compact basis"); return data(); }
    Complex *end() { return empty() ? data() : data() + size(); }
    const Complex *end() const { return empty() ? data() : data() + size(); }
    Complex &operator[](size_t i) {
        if (!chiral) return data()[i];
        if ((i%48)/24 != ((i/48)%12)/6) return structural_zero;
        return data()[(i/48)*24+i%24];
    }
    const Complex &operator[](size_t i) const {
        if (!chiral) return data()[i];
        if ((i%48)/24 != ((i/48)%12)/6) return structural_zero;
        return data()[(i/48)*24+i%24];
    }
    void resize(size_t count) {
        if (shared) {
            if (count != shared_count)
                throw std::runtime_error("cannot resize a shared coefficient window");
        } else
            owned.resize(count);
    }
    void assign(size_t count, Complex value) {
        resize(count);
        std::fill(begin(), end(), value);
    }
};

inline void read_binary(const std::string &path, CoefficientField &field) {
    Field temporary(field.size());
    read_binary(path, temporary);
    field.resize(temporary.size());
    std::copy(temporary.begin(), temporary.end(), field.begin());
}
inline void dump(const std::string &path, const CoefficientField &field) {
    dump(path, Field(field.begin(), field.end()));
}
