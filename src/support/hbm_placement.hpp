#pragma once
// Linux NUMA placement for caller-selected owned hot ranges. No global state,
// allocation, MPI, or implicit fallback to a node outside the allowed mems.
#include <algorithm>
#include <cerrno>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <limits>
#include <set>
#include <sstream>
#include <string>
#include <vector>
#ifdef __linux__
#include <linux/mempolicy.h>
#include <sys/syscall.h>
#include <unistd.h>
#endif

namespace lqcd_native::hbm {
enum class Mode { Off, Prefer, Require };
struct Node {
    int id = -1;
    bool memory_only = false;
    // Indexed by physical node ID, as exported by sysfs distance.
    std::vector<int> distances;
};
struct Plan {
    Mode mode = Mode::Off;
    int cpu_node = -1, memory_node = -1;
    std::string error;
    // memory-only + distance is a candidate heuristic, NOT hardware-type proof.
};
struct Range {
    void *data = nullptr;
    std::size_t bytes = 0;
};
struct AlignedRange {
    std::uintptr_t begin = 0;
    std::size_t bytes = 0;
};
struct Report {
    int memory_node = -1;
    std::size_t requested_bytes = 0, eligible_bytes = 0, bound_bytes = 0;
    std::size_t sampled_pages = 0, resident_on_target = 0, elsewhere = 0, unknown = 0;
    long mbind_rc = 0, query_rc = 0;
    int mbind_errno = 0, query_errno = 0;
    std::vector<int> page_status;
    bool attempted = false, requirement_met = false;
    std::string error;
};

inline bool parse_list(const std::string &text, std::set<int> &out) {
    out.clear();
    if (text.empty())
        return true;
    std::istringstream input(text);
    std::string item;
    if (text.back() == ',')
        return false;
    while (std::getline(input, item, ',')) {
        const auto dash = item.find('-');
        auto number = [](const std::string &s, int &value) {
            if (s.empty() || s.find_first_not_of("0123456789") != std::string::npos)
                return false;
            try {
                const auto n = std::stoul(s);
                if (n > 1048575)
                    return false;
                value = n;
            } catch (...) {
                return false;
            }
            return true;
        };
        int first, last;
        if (!number(item.substr(0, dash), first))
            return false;
        last = first;
        if (dash != std::string::npos && !number(item.substr(dash + 1), last))
            return false;
        if (last < first)
            return false;
        for (int n = first; n <= last; ++n)
            out.insert(n);
    }
    return true;
}
inline AlignedRange full_pages(Range range, std::size_t page) {
    if (!range.data || !page || !range.bytes)
        return {};
    const auto start = reinterpret_cast<std::uintptr_t>(range.data);
    if (range.bytes > std::numeric_limits<std::uintptr_t>::max() - start)
        return {};
    const auto end = start + range.bytes;
    const auto offset = (page - start % page) % page;
    if (offset > range.bytes)
        return {};
    const auto begin = start + offset;
    const auto finish = end - end % page;
    return finish > begin ? AlignedRange{begin, finish - begin} : AlignedRange{};
}
inline Plan select(Mode mode, int cpu, const std::vector<Node> &nodes,
                   const std::set<int> &allowed) {
    Plan plan{mode, cpu, -1, {}};
    if (mode == Mode::Off)
        return plan;
    const auto source =
        std::find_if(nodes.begin(), nodes.end(), [cpu](const Node &n) { return n.id == cpu; });
    if (source == nodes.end() || source->memory_only) {
        plan.error = "CPU NUMA node missing or memory-only";
        return plan;
    }
    int best = std::numeric_limits<int>::max();
    bool tie = false;
    for (const auto &n : nodes) {
        if (!n.memory_only || !allowed.count(n.id) || n.id < 0 ||
            (std::size_t)n.id >= source->distances.size())
            continue;
        const int distance = source->distances[n.id];
        if (distance <= 0)
            continue;
        if (distance < best) {
            best = distance;
            plan.memory_node = n.id;
            tie = false;
        } else if (distance == best)
            tie = true;
    }
    if (plan.memory_node < 0)
        plan.error = "no allowed memory-only NUMA candidate";
    else if (tie) {
        plan.memory_node = -1;
        plan.error = "ambiguous nearest memory-only nodes";
    }
    return plan;
}
inline std::string read_text(const std::string &path) {
    std::ifstream in(path);
    std::ostringstream s;
    s << in.rdbuf();
    std::string text = s.str();
    while (!text.empty() && (text.back() == '\n' || text.back() == '\r'))
        text.pop_back();
    return text;
}
inline bool allowed_mems(std::set<int> &allowed) {
    std::ifstream in("/proc/self/status");
    std::string line;
    while (std::getline(in, line))
        if (line.compare(0, 18, "Mems_allowed_list:") == 0) {
            const auto pos = line.find_first_not_of(" \t", line.find(':') + 1);
            return pos != std::string::npos && parse_list(line.substr(pos), allowed);
        }
    return false;
}
inline Plan from_environment() {
    const char *raw = std::getenv("LQCD_HBM");
    const std::string mode = raw ? raw : "off";
    if (mode == "off")
        return {};
    if (mode != "prefer" && mode != "require") {
        Plan p;
        p.error = "LQCD_HBM must be off/prefer/require";
        return p;
    }
    Plan p;
    p.mode = mode == "require" ? Mode::Require : Mode::Prefer;
    std::set<int> cpu, allowed, online, memory;
    const char *node = std::getenv("LQCD_NUMA_NODE");
    if (!node || !parse_list(node, cpu) || cpu.size() != 1) {
        p.error = "LQCD_NUMA_NODE must identify one CPU NUMA node";
        return p;
    }
    if (!allowed_mems(allowed) ||
        !parse_list(read_text("/sys/devices/system/node/online"), online) ||
        !parse_list(read_text("/sys/devices/system/node/has_memory"), memory)) {
        p.error = "cannot read allowed mems/sysfs NUMA inventory";
        return p;
    }
    std::vector<Node> nodes;
    for (int id : online) {
        const std::string base = "/sys/devices/system/node/node" + std::to_string(id);
        std::ifstream cpus(base + "/cpulist");
        if (!cpus)
            continue; // unreadable is not evidence for memory-only
        Node n;
        n.id = id;
        n.memory_only = memory.count(id) && read_text(base + "/cpulist").empty();
        std::istringstream distances(read_text(base + "/distance"));
        int d;
        // sysfs distances are ordered by online node IDs, including sparse IDs.
        n.distances.resize(online.empty() ? 0 : *online.rbegin() + 1, 0);
        for (int target : online) {
            if (!(distances >> d))
                break;
            n.distances[target] = d;
        }
        nodes.push_back(n);
    }
    return select(p.mode, *cpu.begin(), nodes, allowed);
}

// Return errors instead of throwing: caller must aggregate require-mode failure
// collectively BEFORE any rank proceeds into another MPI solve/setup collective.
inline Report place(const Plan &plan, Range range, std::size_t max_samples = 64) {
    Report r;
    r.memory_node = plan.memory_node;
    r.requested_bytes = range.bytes;
    if (!plan.error.empty()) {
        r.error = plan.error;
        return r;
    }
    if (plan.mode == Mode::Off) {
        r.requirement_met = true;
        return r;
    }
#ifdef __linux__
#if defined(SYS_mbind) && defined(SYS_move_pages)
    const long page = sysconf(_SC_PAGESIZE);
    if (page <= 0) {
        r.error = "page size unavailable";
        return r;
    }
    const auto a = full_pages(range, page);
    r.eligible_bytes = a.bytes;
    if (!a.bytes) {
        r.requirement_met = true;
        return r;
    }
    std::set<int> allowed;
    if (plan.memory_node < 0 || !allowed_mems(allowed) || !allowed.count(plan.memory_node)) {
        r.error = "target no longer in Mems_allowed_list";
        return r;
    }
    constexpr auto bits = sizeof(unsigned long) * 8;
    std::vector<unsigned long> mask((std::size_t)plan.memory_node / bits + 1, 0);
    mask[plan.memory_node / bits] |= 1ul << (plan.memory_node % bits);
    r.attempted = true;
    errno = 0;
    // STRICT makes a partial migration visible rather than silently succeeding.
    r.mbind_rc =
        syscall(SYS_mbind, reinterpret_cast<void *>(a.begin), a.bytes, MPOL_BIND, mask.data(),
                (unsigned long)plan.memory_node + 1, MPOL_MF_MOVE | MPOL_MF_STRICT);
    r.mbind_errno = r.mbind_rc < 0 ? errno : 0;
    if (r.mbind_rc == 0)
        r.bound_bytes = a.bytes;
    const auto pages = a.bytes / page;
    r.sampled_pages = std::min(pages, max_samples);
    std::vector<void *> addresses(r.sampled_pages);
    r.page_status.resize(r.sampled_pages, -EIO);
    for (std::size_t i = 0; i < r.sampled_pages; ++i)
        addresses[i] = reinterpret_cast<void *>(a.begin + (i * (pages / r.sampled_pages)) * page);
    if (r.sampled_pages) {
        errno = 0;
        r.query_rc = syscall(SYS_move_pages, 0, (unsigned long)addresses.size(), addresses.data(),
                             nullptr, r.page_status.data(), 0); // query only
        r.query_errno = r.query_rc < 0 ? errno : 0;
        for (int status : r.page_status) {
            if (r.query_rc < 0 || status < 0)
                ++r.unknown;
            else if (status == plan.memory_node)
                ++r.resident_on_target;
            else
                ++r.elsewhere;
        }
    }
    r.requirement_met =
        r.mbind_rc == 0 && r.sampled_pages > 0 && r.resident_on_target == r.sampled_pages;
    if (!r.requirement_met)
        r.error = "migration or sampled residency verification incomplete";
#else
    r.error = "NUMA placement syscalls unavailable";
#endif
#else
    r.error = "HBM placement requires Linux";
#endif
    return r;
}
} // namespace lqcd_native::hbm
