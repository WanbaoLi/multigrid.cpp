#pragma once
#include "core/field.h"
#include <algorithm>
#include <memory>
#include <stdexcept>
#include <string>
#include <sys/mman.h>

// Coefficients can own ordinary storage or view a collectively managed window.
// Spinors remain independent std::vectors. This class never makes MPI calls.
class CoefficientField {
    Field owned;
    Complex *shared = nullptr;
    size_t shared_count = 0;
    std::shared_ptr<void> owner;

  public:
    using value_type = Complex;
    CoefficientField() = default;
    CoefficientField(const CoefficientField &other)
        : owned(other.shared ? Field{} : Field(other.begin(), other.end())), shared(other.shared),
          shared_count(other.shared_count), owner(other.owner) {}
    CoefficientField &operator=(const CoefficientField &other) {
        if (this != &other) {
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
    void reserve_sparse(size_t count) {
        const size_t bytes = count * sizeof(Complex);
        void *p = mmap(nullptr, bytes, PROT_READ | PROT_WRITE,
                       MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE, -1, 0);
        if (p == MAP_FAILED)
            throw std::bad_alloc();
        bind_shared(static_cast<Complex *>(p), count,
                    std::shared_ptr<void>(p, [bytes](void *q) { munmap(q, bytes); }));
    }
    bool is_shared() const { return shared != nullptr; }
    void release_storage() {
        Field().swap(owned);
        shared = nullptr; shared_count = 0; owner.reset();
    }
    size_t size() const { return shared ? shared_count : owned.size(); }
    bool empty() const { return size() == 0; }
    Complex *data() { return shared ? shared : owned.data(); }
    const Complex *data() const { return shared ? shared : owned.data(); }
    Complex *begin() { return data(); }
    const Complex *begin() const { return data(); }
    Complex *end() { return empty() ? data() : data() + size(); }
    const Complex *end() const { return empty() ? data() : data() + size(); }
    Complex &operator[](size_t i) { return data()[i]; }
    const Complex &operator[](size_t i) const { return data()[i]; }
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
