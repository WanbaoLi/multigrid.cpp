// Independent register-resident CPU FMA throughput benchmark. No solver code.
// Build ON the target: c++ -O3 -std=c++17 -march=native -pthread fma_bench.cpp -o fma_bench
#include <algorithm>
#include <atomic>
#include <cerrno>
#include <chrono>
#include <cmath>
#include <condition_variable>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <mutex>
#include <sched.h>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <time.h>
#include <unistd.h>
#include <vector>
#if defined(__aarch64__) && defined(__ARM_FEATURE_SVE)
#include <arm_sve.h>
#include <sys/prctl.h>
#include <linux/prctl.h>
#endif

#define LIST16(M) M(0) M(1) M(2) M(3) M(4) M(5) M(6) M(7) M(8) M(9) M(10) M(11) M(12) M(13) M(14) M(15)
#define LIST24(M) LIST16(M) M(16) M(17) M(18) M(19) M(20) M(21) M(22) M(23)
#define ARM_CLOBBERS "v0", "v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8", "v9", "v10", "v11", "v12", "v13", "v14", "v15", "v16", "v17", "v18", "v19", "v20", "v21", "v22", "v23", "v24", "v25", "v26"

namespace {
constexpr int accumulator_count =
#if defined(__aarch64__)
    24;
#else
    16;
#endif

// Each iteration contains two passes: x <- fma(+1/2, 2^-10, x),
// then x <- fma(-1/2, 2^-10, x). Starting at one, both operations are
// exactly representable, avoiding overflow, subnormals and FP32 saturation.
// Inline assembly makes every FMA observable even though each pair cancels.
#if defined(__aarch64__) && defined(__ARM_FEATURE_SVE)
constexpr const char *isa_name = "aarch64-sve";
#define SVE_INIT(N) "mov z" #N ".d, z0.d\n\t"
#define SVE_ADD32(N) "fmla z" #N ".s, p0/m, z24.s, z25.s\n\t"
#define SVE_SUB32(N) "fmla z" #N ".s, p0/m, z26.s, z25.s\n\t"
#define SVE_ADD64(N) "fmla z" #N ".d, p0/m, z24.d, z25.d\n\t"
#define SVE_SUB64(N) "fmla z" #N ".d, p0/m, z26.d, z25.d\n\t"
#define SVE_STORE32(N) "st1w {z" #N ".s}, p0, [%[out]]\n\taddvl %[out], %[out], #1\n\t"
#define SVE_STORE64(N) "st1d {z" #N ".d}, p0, [%[out]]\n\taddvl %[out], %[out], #1\n\t"
__attribute__((noinline)) void kernel32(uint64_t count, float *out) {
    const uint32_t one=0x3f800000u, pos=0x3f000000u, delta=0x3a800000u, neg=0xbf000000u;
    asm volatile(
        "ptrue p0.s\n\tdup z0.s, %w[one]\n\t"
        LIST24(SVE_INIT)
        "dup z24.s, %w[pos]\n\tdup z25.s, %w[delta]\n\tdup z26.s, %w[neg]\n\t"
        "1:\n\t" LIST24(SVE_ADD32) LIST24(SVE_SUB32)
        "subs %[count], %[count], #1\n\tb.ne 1b\n\t"
        LIST24(SVE_STORE32)
        : [count] "+&r"(count), [out] "+&r"(out)
        : [one] "r"(one), [pos] "r"(pos), [delta] "r"(delta), [neg] "r"(neg)
        : ARM_CLOBBERS, "p0", "cc", "memory");
}
__attribute__((noinline)) void kernel64(uint64_t count, double *out) {
    const uint64_t one=0x3ff0000000000000ull, pos=0x3fe0000000000000ull;
    const uint64_t delta=0x3f50000000000000ull, neg=0xbfe0000000000000ull;
    asm volatile(
        "ptrue p0.d\n\tdup z0.d, %[one]\n\t"
        LIST24(SVE_INIT)
        "dup z24.d, %[pos]\n\tdup z25.d, %[delta]\n\tdup z26.d, %[neg]\n\t"
        "1:\n\t" LIST24(SVE_ADD64) LIST24(SVE_SUB64)
        "subs %[count], %[count], #1\n\tb.ne 1b\n\t"
        LIST24(SVE_STORE64)
        : [count] "+&r"(count), [out] "+&r"(out)
        : [one] "r"(one), [pos] "r"(pos), [delta] "r"(delta), [neg] "r"(neg)
        : ARM_CLOBBERS, "p0", "cc", "memory");
}
int vector_bytes() { return int(svcntb()); }
int sve_prctl_bytes() { const int v=prctl(PR_SVE_GET_VL); return v < 0 ? -1 : v & PR_SVE_VL_LEN_MASK; }
#elif defined(__aarch64__)
constexpr const char *isa_name = "aarch64-neon";
#define NEON_INIT(N) "mov v" #N ".16b, v0.16b\n\t"
#define NEON_ADD32(N) "fmla v" #N ".4s, v24.4s, v25.4s\n\t"
#define NEON_SUB32(N) "fmla v" #N ".4s, v26.4s, v25.4s\n\t"
#define NEON_ADD64(N) "fmla v" #N ".2d, v24.2d, v25.2d\n\t"
#define NEON_SUB64(N) "fmla v" #N ".2d, v26.2d, v25.2d\n\t"
#define NEON_STORE(N) "str q" #N ", [%[out]], #16\n\t"
__attribute__((noinline)) void kernel32(uint64_t count, float *out) {
    const uint32_t one=0x3f800000u, pos=0x3f000000u, delta=0x3a800000u, neg=0xbf000000u;
    asm volatile(
        "dup v0.4s, %w[one]\n\t" LIST24(NEON_INIT)
        "dup v24.4s, %w[pos]\n\tdup v25.4s, %w[delta]\n\tdup v26.4s, %w[neg]\n\t"
        "1:\n\t" LIST24(NEON_ADD32) LIST24(NEON_SUB32)
        "subs %[count], %[count], #1\n\tb.ne 1b\n\t" LIST24(NEON_STORE)
        : [count] "+&r"(count), [out] "+&r"(out)
        : [one] "r"(one), [pos] "r"(pos), [delta] "r"(delta), [neg] "r"(neg)
        : ARM_CLOBBERS, "cc", "memory");
}
__attribute__((noinline)) void kernel64(uint64_t count, double *out) {
    const uint64_t one=0x3ff0000000000000ull, pos=0x3fe0000000000000ull;
    const uint64_t delta=0x3f50000000000000ull, neg=0xbfe0000000000000ull;
    asm volatile(
        "dup v0.2d, %[one]\n\t" LIST24(NEON_INIT)
        "dup v24.2d, %[pos]\n\tdup v25.2d, %[delta]\n\tdup v26.2d, %[neg]\n\t"
        "1:\n\t" LIST24(NEON_ADD64) LIST24(NEON_SUB64)
        "subs %[count], %[count], #1\n\tb.ne 1b\n\t" LIST24(NEON_STORE)
        : [count] "+&r"(count), [out] "+&r"(out)
        : [one] "r"(one), [pos] "r"(pos), [delta] "r"(delta), [neg] "r"(neg)
        : ARM_CLOBBERS, "cc", "memory");
}
int vector_bytes() { return 16; }
int sve_prctl_bytes() { return 0; }
#elif defined(__x86_64__) && defined(__AVX512F__)
constexpr const char *isa_name = "x86-avx512-fma";
#define X86_INIT(N) "vmovaps %%zmm19, %%zmm" #N "\n\t"
#define X86_ADD32(N) "vfmadd231ps %%zmm16, %%zmm17, %%zmm" #N "\n\t"
#define X86_SUB32(N) "vfmadd231ps %%zmm18, %%zmm17, %%zmm" #N "\n\t"
#define X86_ADD64(N) "vfmadd231pd %%zmm16, %%zmm17, %%zmm" #N "\n\t"
#define X86_SUB64(N) "vfmadd231pd %%zmm18, %%zmm17, %%zmm" #N "\n\t"
#define X86_STORE32(N) "vmovups %%zmm" #N ", " #N "*64(%[out])\n\t"
#define X86_STORE64(N) "vmovupd %%zmm" #N ", " #N "*64(%[out])\n\t"
#define X86_CLOBBERS "zmm0", "zmm1", "zmm2", "zmm3", "zmm4", "zmm5", "zmm6", "zmm7", "zmm8", "zmm9", "zmm10", "zmm11", "zmm12", "zmm13", "zmm14", "zmm15", "zmm16", "zmm17", "zmm18", "zmm19", "cc", "memory"
__attribute__((noinline)) void kernel32(uint64_t count, float *out) {
    const float c[4] = {1.f, .5f, 0x1p-10f, -.5f};
    asm volatile(
        "vbroadcastss 0(%[c]), %%zmm19\n\t" LIST16(X86_INIT)
        "vbroadcastss 4(%[c]), %%zmm16\n\tvbroadcastss 8(%[c]), %%zmm17\n\tvbroadcastss 12(%[c]), %%zmm18\n\t"
        "1:\n\t" LIST16(X86_ADD32) LIST16(X86_SUB32)
        "sub $1, %[count]\n\tjnz 1b\n\t" LIST16(X86_STORE32)
        "vzeroupper\n\t"
        : [count] "+&r"(count)
        : [out] "r"(out), [c] "r"(c)
        : X86_CLOBBERS);
}
__attribute__((noinline)) void kernel64(uint64_t count, double *out) {
    const double c[4] = {1., .5, 0x1p-10, -.5};
    asm volatile(
        "vbroadcastsd 0(%[c]), %%zmm19\n\t" LIST16(X86_INIT)
        "vbroadcastsd 8(%[c]), %%zmm16\n\tvbroadcastsd 16(%[c]), %%zmm17\n\tvbroadcastsd 24(%[c]), %%zmm18\n\t"
        "1:\n\t" LIST16(X86_ADD64) LIST16(X86_SUB64)
        "sub $1, %[count]\n\tjnz 1b\n\t" LIST16(X86_STORE64)
        "vzeroupper\n\t"
        : [count] "+&r"(count)
        : [out] "r"(out), [c] "r"(c)
        : X86_CLOBBERS);
}
int vector_bytes() { return 64; }
int sve_prctl_bytes() { return 0; }
#else
#error "Supported targets: AArch64 SVE/NEON or x86-64 AVX512F. Compile on the actual target with -march=native."
#endif

double now() {
    timespec t{};
    if (clock_gettime(CLOCK_MONOTONIC_RAW, &t)) throw std::runtime_error("clock_gettime failed");
    return double(t.tv_sec) + double(t.tv_nsec) * 1e-9;
}
class Barrier {
    std::mutex mutex;
    std::condition_variable ready;
    size_t count, waiting=0, generation=0;
public:
    explicit Barrier(size_t n) : count(n) {}
    void wait() {
        std::unique_lock<std::mutex> lock(mutex);
        const size_t previous=generation;
        if (++waiting == count) { waiting=0; ++generation; ready.notify_all(); }
        else ready.wait(lock, [&]{ return generation != previous; });
    }
};
std::string escaped(const std::string &s) {
    std::ostringstream out;
    out << '"';
    for (const unsigned char ch : s) {
        if (ch=='"' || ch=='\\') out << '\\' << ch;
        else if (ch=='\n') out << "\\n";
        else if (ch < 32) out << '?';
        else out << ch;
    }
    out << '"';
    return out.str();
}
std::vector<int> parse_cpus(const std::string &value) {
    std::vector<int> out;
    std::istringstream input(value);
    std::string part;
    while (std::getline(input, part, ',')) {
        size_t consumed=0;
        int cpu=std::stoi(part, &consumed);
        if (consumed != part.size() || cpu<0 || cpu>=CPU_SETSIZE)
            throw std::runtime_error("Invalid CPU list (use explicit comma-separated IDs)");
        out.push_back(cpu);
    }
    if (out.empty() || std::set<int>(out.begin(),out.end()).size()!=out.size())
        throw std::runtime_error("CPU list is empty or contains duplicates");
    return out;
}
std::string read_one(const std::string &path) {
    std::ifstream f(path);
    std::string value;
    if (!std::getline(f,value)) throw std::runtime_error("Cannot read topology: "+path);
    return value;
}
void physical_cpus_only(const std::vector<int> &cpus) {
    cpu_set_t allowed;
    CPU_ZERO(&allowed);
    if (sched_getaffinity(0,sizeof(allowed),&allowed)) throw std::runtime_error("sched_getaffinity failed");
    std::set<std::pair<std::string,std::string>> cores;
    for (const int cpu : cpus) {
        if (!CPU_ISSET(cpu,&allowed)) throw std::runtime_error("Requested CPU outside allowed affinity");
        const std::string prefix="/sys/devices/system/cpu/cpu"+std::to_string(cpu)+"/topology/";
        if (!cores.emplace(read_one(prefix+"physical_package_id"),read_one(prefix+"core_id")).second)
            throw std::runtime_error("CPU list includes SMT siblings of the same physical core");
    }
}
struct Sample {
    uint64_t iterations=0;
    double start=0, end=0, checksum=0, max_error=0;
    int cpu_start=-1, cpu_end=-1;
};
struct Worker {
    int requested_cpu=-1, actual_cpu=-1, affinity_width=0, vector_bytes=0, sve_vl_bytes=0;
    std::string error;
    std::vector<Sample> samples;
};
template<class T> void run_kernel(uint64_t n,T *out);
template<> void run_kernel<float>(uint64_t n,float *out) { kernel32(n,out); }
template<> void run_kernel<double>(uint64_t n,double *out) { kernel64(n,out); }

template<class T> int benchmark(const std::vector<int> &cpus, double seconds, int repeats) {
    Barrier barrier(cpus.size());
    std::atomic<bool> setup_failed{false};
    std::vector<Worker> workers(cpus.size());
    std::vector<std::thread> pool;
    pool.reserve(cpus.size());
    for (size_t id=0; id<cpus.size(); ++id) {
        workers[id].requested_cpu=cpus[id];
        workers[id].samples.resize(repeats);
        pool.emplace_back([&,id] {
            Worker &w=workers[id];
            cpu_set_t set;
            CPU_ZERO(&set); CPU_SET(cpus[id],&set);
            if (sched_setaffinity(0,sizeof(set),&set)) {
                w.error=std::string("sched_setaffinity: ")+strerror(errno);
                setup_failed=true;
            }
            CPU_ZERO(&set);
            if (sched_getaffinity(0,sizeof(set),&set)) { w.error="sched_getaffinity failed"; setup_failed=true; }
            w.affinity_width=CPU_COUNT(&set);
            w.actual_cpu=sched_getcpu();
            w.vector_bytes=vector_bytes(); w.sve_vl_bytes=sve_prctl_bytes();
            if (w.actual_cpu!=cpus[id] || w.affinity_width!=1 ||
                (w.sve_vl_bytes>0 && w.sve_vl_bytes!=w.vector_bytes)) {
                w.error="CPU affinity or per-thread SVE width mismatch";
                setup_failed=true;
            }
            const int lanes=w.vector_bytes/sizeof(T);
            std::vector<T> output(accumulator_count*lanes, T(0));
            barrier.wait();
            if (setup_failed) return;
            // Calibrate concurrently at the requested thread count. No clock calls
            // occur in the assembly loop; only complete kernel calls are timed.
            uint64_t iterations=4096;
            double elapsed=0;
            do {
                const double start=now();
                run_kernel(iterations,output.data());
                elapsed=now()-start;
                if (elapsed < .04) iterations*=2;
            } while (elapsed < .04 && iterations < (1ull<<40));
            const long double estimate=static_cast<long double>(iterations)*seconds/std::max(elapsed,1e-9);
            iterations=std::max<uint64_t>(1,static_cast<uint64_t>(std::min<long double>(estimate,1ull<<44)));
            for (int r=0; r<repeats; ++r) {
                barrier.wait();
                Sample &s=w.samples[r];
                s.iterations=iterations;
                s.cpu_start=sched_getcpu();
                s.start=now();
                run_kernel(iterations,output.data());
                s.end=now();
                s.cpu_end=sched_getcpu();
                for (const T x : output) {
                    if (!std::isfinite(x)) w.error="Nonfinite FMA output";
                    s.checksum+=static_cast<double>(x);
                    s.max_error=std::max(s.max_error,std::abs(static_cast<double>(x)-1.));
                }
                if (!std::isfinite(s.checksum) || s.max_error > (sizeof(T)==4 ? 1e-6 : 1e-13))
                    w.error="FMA checksum verification failed";
                if (s.cpu_start!=cpus[id] || s.cpu_end!=cpus[id]) w.error="Worker migrated off requested CPU";
                barrier.wait();
            }
        });
    }
    for (auto &thread : pool) thread.join();
    bool pass=!setup_failed;
    for (const auto &w : workers) pass=pass && w.error.empty();
    char hostname[256]{}; gethostname(hostname,sizeof(hostname)-1);
    std::cout << std::setprecision(17)
              << "{\"schema\":\"cpu-register-fma-v1\",\"status\":" << escaped(pass?"PASS":"FAIL")
              << ",\"hostname\":" << escaped(hostname) << ",\"isa\":" << escaped(isa_name)
              << ",\"precision\":" << escaped(sizeof(T)==4?"fp32":"fp64")
              << ",\"compiler\":" << escaped(__VERSION__)
              << ",\"threads\":" << cpus.size() << ",\"target_seconds\":" << seconds
              << ",\"repeats\":" << repeats << ",\"accumulators\":" << accumulator_count
              << ",\"fma_passes_per_iteration\":2,\"flops_per_fma_per_lane\":2"
              << ",\"clock\":\"CLOCK_MONOTONIC_RAW\",\"fma_pattern\":\"x+=0.5*2^-10; x+=(-0.5)*2^-10\""
              << ",\"workers\":[";
    for (size_t id=0; id<workers.size(); ++id) {
        const auto &w=workers[id];
        if (id) std::cout << ',';
        std::cout << "{\"requested_cpu\":" << w.requested_cpu << ",\"actual_cpu\":" << w.actual_cpu
                  << ",\"affinity_width\":" << w.affinity_width << ",\"vector_bytes\":" << w.vector_bytes
                  << ",\"sve_vl_bytes\":" << w.sve_vl_bytes << ",\"error\":" << escaped(w.error) << '}';
    }
    std::cout << "],\"samples\":[";
    std::vector<double> rates;
    for (int r=0; r<repeats && !setup_failed; ++r) {
        double first=std::numeric_limits<double>::infinity(), last=0, total_flops=0;
        for (const auto &w : workers) {
            const auto &s=w.samples[r];
            first=std::min(first,s.start); last=std::max(last,s.end);
            total_flops+=static_cast<double>(s.iterations)*accumulator_count*2*2*(w.vector_bytes/sizeof(T));
        }
        const double wall=last-first, gflops=total_flops/wall/1e9;
        rates.push_back(gflops);
        if (r) std::cout << ',';
        std::cout << "{\"repeat\":" << r+1 << ",\"seconds\":" << wall
                  << ",\"flops\":" << total_flops << ",\"gflops\":" << gflops << ",\"threads\":[";
        for (size_t id=0; id<workers.size(); ++id) {
            const auto &s=workers[id].samples[r];
            if (id) std::cout << ',';
            std::cout << "{\"cpu\":" << cpus[id] << ",\"iterations\":" << s.iterations
                      << ",\"start\":" << s.start << ",\"end\":" << s.end << ",\"seconds\":" << s.end-s.start
                      << ",\"cpu_start\":" << s.cpu_start << ",\"cpu_end\":" << s.cpu_end
                      << ",\"checksum\":" << s.checksum << ",\"max_abs_error\":" << s.max_error << '}';
        }
        std::cout << "]}";
    }
    std::cout << ']';
    if (!rates.empty()) {
        std::sort(rates.begin(),rates.end());
        const double median=rates.size()%2 ? rates[rates.size()/2] : .5*(rates[rates.size()/2-1]+rates[rates.size()/2]);
        std::cout << ",\"median_gflops\":" << median << ",\"max_gflops\":" << rates.back();
    }
    std::cout << "}\n";
    return pass?0:1;
}
} // namespace

int main(int argc,char **argv) {
    try {
        std::vector<int> cpus;
        std::string precision;
        double seconds=1.; int repeats=3;
        for (int i=1;i<argc;i+=2) {
            if (i+1>=argc) throw std::runtime_error("Every option requires a value");
            const std::string key=argv[i], value=argv[i+1];
            if (key=="--cpus") cpus=parse_cpus(value);
            else if (key=="--precision") precision=value;
            else if (key=="--seconds") seconds=std::stod(value);
            else if (key=="--repeats") repeats=std::stoi(value);
            else throw std::runtime_error("Unknown option: "+key);
        }
        if (cpus.empty() || (precision!="fp32" && precision!="fp64") ||
            !(seconds>=.05 && seconds<=30) || repeats<1 || repeats>20)
            throw std::runtime_error("Usage: fma_bench --cpus 0,1,... --precision fp32|fp64 [--seconds 1] [--repeats 3]");
        physical_cpus_only(cpus);
        return precision=="fp32" ? benchmark<float>(cpus,seconds,repeats) : benchmark<double>(cpus,seconds,repeats);
    } catch (const std::exception &e) {
        std::cout << "{\"schema\":\"cpu-register-fma-v1\",\"status\":\"ERROR\",\"error\":" << escaped(e.what()) << "}\n";
        return 2;
    }
}
