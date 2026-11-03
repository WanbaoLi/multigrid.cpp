// Auxiliary scheduling experiment, not a solver change or acceptance result.
// Run pinned to one NUMA domain with the real compute-node GCC/OpenMP runtime:
// g++ -O3 -std=c++17 -march=native -fopenmp team_probe.cpp -o team_probe
// ./team_probe --threads 37 --rounds 100
// Each alternation does the same 64-block payload three times: full team,
// candidate coarse team, restored full team. Fixed-team control does not call
// omp_set_num_threads inside its timed loop. All other cases do so explicitly.
#include <omp.h>
#include <sys/resource.h>
#include <sched.h>
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using Clock = std::chrono::steady_clock;
constexpr int blocks = 64, components = 96, recurrence_steps = 32;
using Field = std::array<float, blocks * components>;
double now() {
    return std::chrono::duration<double>(Clock::now().time_since_epoch()).count();
}
std::string quote(const std::string &s) {
    std::string out = "\"";
    for (unsigned char c : s) {
        if (c == '\\' || c == '"') { out += '\\'; out += c; }
        else if (c == '\n') out += "\\n";
        else if (c == '\r') out += "\\r";
        else if (c == '\t') out += "\\t";
        else if (c < 32) out += '?';
        else out += c;
    }
    return out + '"';
}
void budget(double deadline) {
    if (now() > deadline) throw std::runtime_error("27-second auxiliary probe budget exhausted");
}

// Small independent blocks and a working set below one core's L2 capacity.
// This is arithmetic plus repeated parallel-region scheduling, not a dense
// matrix benchmark or a model of the complete MG coarse solve.
void block_payload(const Field &input, Field &output, int block) {
#pragma omp simd
    for (int component = 0; component < components; ++component) {
        const int index = block * components + component;
        const float original = input[index];
        float value = original;
        for (int step = 0; step < recurrence_steps; ++step)
            value = value * (.99991f + float(step % 3) * .00001f) +
                    original * .0002f + float(step % 5 - 2) * .00001f;
        output[index] = value;
    }
    asm volatile("" : : "r"(output.data()) : "memory");
}
int phase(const Field &input, Field &output, std::vector<int> *cpus = nullptr) {
    int actual = 0;
#pragma omp parallel for schedule(static)
    for (int block = 0; block < blocks; ++block) {
        if (block == 0) actual = omp_get_num_threads();
        if (cpus) (*cpus)[omp_get_thread_num()] = sched_getcpu();
        block_payload(input, output, block);
    }
    return actual;
}
void require_team(int actual, int expected) {
    if (actual != expected) throw std::runtime_error("OpenMP team differs from requested size");
}

std::set<int> tids() {
    std::set<int> result;
    for (const auto &entry : std::filesystem::directory_iterator("/proc/self/task")) {
        const auto name = entry.path().filename().string();
        if (!name.empty() && name.find_first_not_of("0123456789") == std::string::npos)
            result.insert(std::stoi(name));
    }
    if (result.empty()) throw std::runtime_error("no /proc/self/task IDs found");
    return result;
}
std::vector<int> difference(const std::set<int> &left, const std::set<int> &right) {
    std::vector<int> result;
    std::set_difference(left.begin(), left.end(), right.begin(), right.end(), std::back_inserter(result));
    return result;
}
template<class Container> void list(const Container &items) {
    bool first = true;
    std::cout << '[';
    for (auto item : items) { if (!first) std::cout << ','; first = false; std::cout << item; }
    std::cout << ']';
}
struct Usage {
    rusage data{};
    Usage() { if (getrusage(RUSAGE_SELF, &data)) throw std::runtime_error("getrusage failed"); }
};
double cpu_seconds(const timeval &time) { return time.tv_sec + time.tv_usec * 1e-6; }
void usage_delta(const Usage &before, const Usage &after) {
    std::cout << "{\"voluntary_context_switches\":" << after.data.ru_nvcsw - before.data.ru_nvcsw
              << ",\"involuntary_context_switches\":" << after.data.ru_nivcsw - before.data.ru_nivcsw
              << ",\"minor_faults\":" << after.data.ru_minflt - before.data.ru_minflt
              << ",\"major_faults\":" << after.data.ru_majflt - before.data.ru_majflt
              << ",\"process_user_cpu_seconds\":" << cpu_seconds(after.data.ru_utime) - cpu_seconds(before.data.ru_utime)
              << ",\"process_system_cpu_seconds\":" << cpu_seconds(after.data.ru_stime) - cpu_seconds(before.data.ru_stime) << '}';
}
struct Sample {
    double seconds_per_alternation;
    std::array<double, 3> phase_seconds_per_alternation;
    Usage before, after;
};

void alternation(const Field &input, std::array<Field, 3> &output,
                 int full, int coarse, bool fixed, std::array<double, 3> *phase_times) {
    for (int part = 0; part < 3; ++part) {
        const int requested = part == 1 ? coarse : full;
        if (!fixed) omp_set_num_threads(requested);
        const double start = now();
        require_team(phase(input, output[part]), requested);
        if (phase_times) (*phase_times)[part] += now() - start;
    }
}
double checksum_and_verify(const std::array<Field, 3> &output, const Field &reference) {
    double checksum = 0;
    for (const Field &field : output)
        for (size_t i = 0; i < reference.size(); ++i) {
            if (!std::isfinite(field[i]) || field[i] != reference[i])
                throw std::runtime_error("identical arithmetic changed across scheduling cases");
            checksum += field[i];
        }
    return checksum;
}
} // namespace

int main(int argc, char **argv) {
    try {
        int full_threads = 37, rounds = 100;
        for (int i = 1; i < argc; ++i) {
            const std::string argument = argv[i];
            if (argument == "--threads" && i + 1 < argc) full_threads = std::stoi(argv[++i]);
            else if (argument == "--rounds" && i + 1 < argc) rounds = std::stoi(argv[++i]);
            else throw std::runtime_error("usage: team_probe [--threads 37] [--rounds 100]");
        }
        if (full_threads < 1 || full_threads > blocks || rounds < 1 || rounds > 100000)
            throw std::runtime_error("threads must be 1..64 and rounds 1..100000");
        const double deadline = now() + 27.;
        omp_set_dynamic(0);
        omp_set_num_threads(full_threads);
        Field input{}, reference{};
        std::array<Field, 3> output{};
        for (size_t i = 0; i < input.size(); ++i) input[i] = (int(i % 97) - 48) * .01f;
        for (int block = 0; block < blocks; ++block) block_payload(input, reference, block);
        std::vector<int> caps{full_threads};
        for (int candidate : {32, 16, 8, 1})
            if (candidate <= full_threads && std::find(caps.begin(), caps.end(), candidate) == caps.end())
                caps.push_back(candidate);
        std::cout << std::setprecision(12)
                  << "{\"complete\":true,\"auxiliary_only\":true,\"compiler\":" << quote(__VERSION__)
                  << ",\"full_threads\":" << full_threads << ",\"rounds_per_sample\":" << rounds
                  << ",\"warmup_alternations\":5,\"blocks_per_phase\":64,\"real_components_per_block\":96,"
                     "\"recurrence_steps_per_component\":32,\"phases_per_alternation\":3,"
                     "\"phase_order\":[\"full_before\",\"coarse_cap\",\"restored_full\"],"
                     "\"tid_snapshot_semantics\":\"immediate_after_join; observed_ID_changes_do_not_prove_runtime_implementation\","
                     "\"results\":[";
        bool first = true;
        for (size_t case_number = 0; case_number <= caps.size(); ++case_number) {
            budget(deadline);
            const bool fixed = case_number == 0;
            const int cap = fixed ? full_threads : caps[case_number - 1];
            omp_set_num_threads(full_threads);
            std::vector<int> full_worker_cpus(full_threads, -1);
            require_team(phase(input, output[0], &full_worker_cpus), full_threads);
            const auto before_ids = tids();
            if (!fixed) omp_set_num_threads(cap);
            const int cap_actual = phase(input, output[1]);
            require_team(cap_actual, cap);
            const auto cap_ids = tids();
            if (!fixed) omp_set_num_threads(full_threads);
            const int restored_actual = phase(input, output[2]);
            require_team(restored_actual, full_threads);
            const auto restored_ids = tids();
            checksum_and_verify(output, reference);
            for (int warm = 0; warm < 5; ++warm)
                alternation(input, output, full_threads, cap, fixed, nullptr);
            std::vector<Sample> samples;
            for (int repeat = 0; repeat < 3; ++repeat) {
                budget(deadline);
                Sample sample{};
                sample.before = Usage();
                std::array<double, 3> phase_times{};
                const double start = now();
                for (int round = 0; round < rounds; ++round) {
                    if (round % 10 == 0) budget(deadline);
                    alternation(input, output, full_threads, cap, fixed, &phase_times);
                }
                sample.seconds_per_alternation = (now() - start) / rounds;
                sample.after = Usage();
                for (int part = 0; part < 3; ++part)
                    sample.phase_seconds_per_alternation[part] = phase_times[part] / rounds;
                checksum_and_verify(output, reference);
                samples.push_back(sample);
            }
            std::vector<double> elapsed;
            for (const auto &sample : samples) elapsed.push_back(sample.seconds_per_alternation);
            std::sort(elapsed.begin(), elapsed.end());
            if (!first) std::cout << ',';
            first = false;
            std::cout << "{\"mode\":" << quote(fixed ? "fixed_control" : "set_cap_and_restore")
                      << ",\"coarse_threads\":" << cap << ",\"actual_coarse_threads\":" << cap_actual
                      << ",\"actual_restored_threads\":" << restored_actual
                      << ",\"full_team_worker_cpus\":";
            list(full_worker_cpus);
            std::cout << ",\"first_pair_tids\":{\"before\":"; list(before_ids);
            std::cout << ",\"after_cap\":"; list(cap_ids);
            std::cout << ",\"after_restore\":"; list(restored_ids);
            const auto missing = difference(before_ids, restored_ids), added = difference(restored_ids, before_ids);
            std::cout << ",\"missing_after_restore\":"; list(missing);
            std::cout << ",\"new_after_restore\":"; list(added);
            std::cout << ",\"missing_count\":" << missing.size() << ",\"new_count\":" << added.size() << '}'
                      << ",\"median_seconds_per_alternation\":" << elapsed[1]
                      << ",\"checksum\":" << checksum_and_verify(output, reference)
                      << ",\"exact_output_match\":true,\"samples\":[";
            for (size_t i = 0; i < samples.size(); ++i) {
                if (i) std::cout << ',';
                const auto &sample = samples[i];
                std::cout << "{\"repeat\":" << i << ",\"seconds_per_alternation\":" << sample.seconds_per_alternation
                          << ",\"phase_seconds_per_alternation\":"; list(sample.phase_seconds_per_alternation);
                std::cout << ",\"getrusage_process_span\":"; usage_delta(sample.before, sample.after);
                std::cout << '}';
            }
            std::cout << "]}";
        }
        budget(deadline);
        std::cout << "]}\n";
        return 0;
    } catch (const std::exception &error) {
        // Interrupted/over-budget output is deliberately not valid complete JSON.
        std::cerr << "team_probe failed: " << error.what() << '\n';
        return 1;
    }
}
