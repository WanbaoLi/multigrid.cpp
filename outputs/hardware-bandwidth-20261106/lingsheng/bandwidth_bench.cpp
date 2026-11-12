// Independent NUMA-bound logical streaming bandwidth benchmark; no solver code.
// Build on target: c++ -O3 -std=c++17 -pthread -march=native bandwidth_bench.cpp -o bandwidth_bench
#include <algorithm>
#include <atomic>
#include <cerrno>
#include <cmath>
#include <condition_variable>
#include <cstdint>
#include <cstring>
#include <dlfcn.h>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <mutex>
#include <sched.h>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <linux/mempolicy.h>
#include <thread>
#include <time.h>
#include <unistd.h>
#include <vector>
#if defined(__aarch64__) && defined(__ARM_FEATURE_SVE)
#include <arm_sve.h>
#include <sys/prctl.h>
#include <linux/prctl.h>
#elif defined(__x86_64__) && defined(__AVX512F__)
#include <immintrin.h>
#endif

namespace {
using SdkVerify = int (*)(void *, std::size_t, int);
void *sdk_handle = nullptr;
SdkVerify sdk_verify = nullptr;
using Mbind = long (*)(void *, unsigned long, int, const unsigned long *, unsigned long, unsigned);
void *numa_handle = nullptr;
Mbind library_mbind = nullptr;
std::string quote(const std::string &s) {
    std::ostringstream o; o << '"';
    for (unsigned char c:s) {
        if(c=='"'||c=='\\') o << '\\' << c;
        else if(c=='\n') o << "\\n";
        else if(c<32) o << '?'; else o << c;
    }
    return o.str()+'"';
}
double now() {
    timespec t{};
    if(clock_gettime(CLOCK_MONOTONIC_RAW,&t)) throw std::runtime_error("clock_gettime failed");
    return double(t.tv_sec)+double(t.tv_nsec)*1e-9;
}
std::string file(const std::string &p) {
    std::ifstream f(p); if(!f) throw std::runtime_error("Cannot read "+p);
    std::ostringstream s; s << f.rdbuf(); return s.str();
}
class Barrier {
    std::mutex m; std::condition_variable cv;
    size_t n,waiting=0,generation=0;
public:
    explicit Barrier(size_t count):n(count){}
    void wait(){ std::unique_lock<std::mutex> lock(m); auto previous=generation;
        if(++waiting==n){waiting=0;++generation;cv.notify_all();}
        else cv.wait(lock,[&]{return generation!=previous;}); }
};
std::set<int> parse_list(const std::string &s) {
    std::set<int> result; std::istringstream in(s); std::string part;
    while(std::getline(in,part,',')){
        if(part.empty())continue; auto dash=part.find('-');
        int a=std::stoi(part),b=dash==std::string::npos?a:std::stoi(part.substr(dash+1));
        if(a<0||b<a)throw std::runtime_error("Invalid CPU/node list");
        for(int x=a;x<=b;++x)result.insert(x);
    } return result;
}
std::set<int> allowed_mems(){
    std::istringstream in(file("/proc/self/status")); std::string line;
    while(std::getline(in,line))if(line.rfind("Mems_allowed_list:",0)==0)
        return parse_list(line.substr(line.find(':')+1));
    throw std::runtime_error("Cannot find allowed memory nodes");
}
struct Entry {int group,cpu,node,group_index=-1,local_rank=-1;};
std::vector<Entry> read_plan(const std::string &path){
    std::ifstream in(path);if(!in)throw std::runtime_error("Cannot open plan");
    cpu_set_t allowed;CPU_ZERO(&allowed);
    if(sched_getaffinity(0,sizeof(allowed),&allowed))throw std::runtime_error("sched_getaffinity failed");
    const auto mems=allowed_mems();std::set<int> cpus;std::set<std::string> physical;
    std::vector<Entry> entries;std::string line;
    while(std::getline(in,line)){
        if(line.empty()||line[0]=='#')continue;
        Entry e{};std::istringstream row(line);std::string extra;
        if(!(row>>e.group>>e.cpu>>e.node)||(row>>extra))throw std::runtime_error("Plan requires group cpu memory_node");
        if(e.cpu<0||e.cpu>=CPU_SETSIZE||!CPU_ISSET(e.cpu,&allowed)||!cpus.insert(e.cpu).second)
            throw std::runtime_error("Requested CPU unavailable or duplicate");
        if(!mems.count(e.node))throw std::runtime_error("Target memory node outside allowed mems");
        auto siblings=file("/sys/devices/system/cpu/cpu"+std::to_string(e.cpu)+"/topology/thread_siblings_list");
        if(!physical.insert(siblings).second)throw std::runtime_error("SMT siblings are not distinct physical cores");
        entries.push_back(e);
    }
    if(entries.empty())throw std::runtime_error("Empty plan");return entries;
}
struct Residency {
    long query_rc=-1;int query_errno=0;size_t samples=0,on_target=0;
    std::string maps_line;std::map<int,uint64_t> node_pages;
    uint64_t mapped_pages=0,kernel_page_bytes=0;bool maps_verified=false,verified=false;
};
struct Array {
    void *mapping=nullptr;double *data=nullptr;size_t bytes=0,mapping_bytes=0;
    int node=-1;long mbind_rc=-1;int mbind_errno=0;Residency before,after;
    int sdk_before=-2,sdk_after=-2;
    Array(size_t size,int target):bytes(size),node(target){
        const size_t page=sysconf(_SC_PAGESIZE);mapping_bytes=bytes+2*page;
        mapping=mmap(nullptr,mapping_bytes,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
        if(mapping==MAP_FAILED){mapping=nullptr;throw std::runtime_error("mmap failed: "+std::string(strerror(errno)));}
        data=reinterpret_cast<double*>(static_cast<char*>(mapping)+page);
        if(mprotect(data,bytes,PROT_READ|PROT_WRITE))throw std::runtime_error("mprotect failed");
        if(madvise(data,bytes,MADV_NOHUGEPAGE))throw std::runtime_error("MADV_NOHUGEPAGE failed");
        constexpr size_t bits=sizeof(unsigned long)*8;
        std::vector<unsigned long> mask(size_t(node)/bits+1,0);mask[node/bits]|=1ul<<(node%bits);
        errno=0;
        mbind_rc=library_mbind(data,bytes,MPOL_BIND,mask.data(),mask.size()*bits,0u);
        mbind_errno=mbind_rc<0?errno:0;
        if(mbind_rc)throw std::runtime_error("libnuma mbind failed for node "+std::to_string(node)+": "+strerror(mbind_errno));
    }
    ~Array(){if(mapping)munmap(mapping,mapping_bytes);}
    Array(const Array&)=delete;Array&operator=(const Array&)=delete;
    Residency query() const {
        Residency r;const size_t page=sysconf(_SC_PAGESIZE),pages=bytes/page;
        r.samples=std::min<size_t>(pages,256);
        std::vector<void*> ptrs(r.samples);std::vector<int> status(r.samples,-1);
        for(size_t i=0;i<r.samples;++i)ptrs[i]=reinterpret_cast<char*>(data)+(i*(pages-1)/std::max<size_t>(1,r.samples-1))*page;
        errno=0;r.query_rc=syscall(SYS_move_pages,0,(unsigned long)r.samples,ptrs.data(),nullptr,status.data(),0);
        r.query_errno=r.query_rc<0?errno:0;
        if(r.query_rc==0)for(int n:status)if(n==node)++r.on_target;
        std::ifstream maps("/proc/self/numa_maps");std::string line;
        const uintptr_t wanted=reinterpret_cast<uintptr_t>(data);
        while(std::getline(maps,line)){
            std::istringstream tokens(line);std::string address,token;tokens>>address;
            uintptr_t start=0;try{start=std::stoull(address,nullptr,16);}catch(...){continue;}
            if(start!=wanted)continue;r.maps_line=line;
            while(tokens>>token){
                if(token.rfind("kernelpagesize_kB=",0)==0)r.kernel_page_bytes=std::stoull(token.substr(18))*1024;
                if(token.size()>2&&token[0]=='N'&&std::isdigit(token[1])){
                    auto equal=token.find('=');if(equal==std::string::npos)continue;
                    int n=std::stoi(token.substr(1,equal-1));uint64_t count=std::stoull(token.substr(equal+1));
                    r.node_pages[n]=count;r.mapped_pages+=count;
                }
            }break;
        }
        // numa_maps N counts are base pages on the tested Linux kernels. NOHUGEPAGE ensures this VMA uses base pages.
        r.maps_verified=r.kernel_page_bytes==page&&r.mapped_pages==pages&&r.node_pages.size()==1&&r.node_pages.count(node);
        r.verified=(r.query_rc==0&&r.on_target==r.samples)||r.maps_verified;
        return r;
    }
};
struct Group {int id,node;std::vector<size_t> workers;std::unique_ptr<Array>a,b,c;};

#if defined(__aarch64__) && defined(__ARM_FEATURE_SVE)
constexpr const char* isa="aarch64-sve";
int vector_bytes(){return svcntb();}
int sve_bytes(){int v=prctl(PR_SVE_GET_VL);return v<0?-1:v&PR_SVE_VL_LEN_MASK;}
__attribute__((noinline)) double read_kernel(const double*b,size_t n){
    const size_t lanes=svcntd();svfloat64_t s0=svdup_f64(0),s1=s0,s2=s0,s3=s0;size_t i=0;
    for(;i+4*lanes<=n;i+=4*lanes){auto p=svptrue_b64();
        s0=svadd_f64_x(p,s0,svld1_f64(p,b+i));s1=svadd_f64_x(p,s1,svld1_f64(p,b+i+lanes));
        s2=svadd_f64_x(p,s2,svld1_f64(p,b+i+2*lanes));s3=svadd_f64_x(p,s3,svld1_f64(p,b+i+3*lanes));}
    double sum=svaddv_f64(svptrue_b64(),svadd_f64_x(svptrue_b64(),svadd_f64_x(svptrue_b64(),s0,s1),svadd_f64_x(svptrue_b64(),s2,s3)));
    for(;i<n;++i)sum+=b[i];return sum;
}
__attribute__((noinline)) void copy_kernel(double*a,const double*b,size_t n){
    for(size_t i=0;i<n;i+=svcntd()){auto p=svwhilelt_b64(i,n);svst1_f64(p,a+i,svld1_f64(p,b+i));}
}
__attribute__((noinline)) void triad_kernel(double*a,const double*b,const double*c,size_t n){
    for(size_t i=0;i<n;i+=svcntd()){auto p=svwhilelt_b64(i,n);auto v=svmla_n_f64_x(p,svld1_f64(p,b+i),svld1_f64(p,c+i),3.);svst1_f64(p,a+i,v);}
}
#elif defined(__x86_64__) && defined(__AVX512F__)
constexpr const char* isa="x86-avx512";
int vector_bytes(){return 64;}int sve_bytes(){return 0;}
__attribute__((noinline)) double read_kernel(const double*b,size_t n){
    __m512d s0=_mm512_setzero_pd(),s1=s0,s2=s0,s3=s0;size_t i=0;
    for(;i+32<=n;i+=32){s0=_mm512_add_pd(s0,_mm512_loadu_pd(b+i));s1=_mm512_add_pd(s1,_mm512_loadu_pd(b+i+8));
        s2=_mm512_add_pd(s2,_mm512_loadu_pd(b+i+16));s3=_mm512_add_pd(s3,_mm512_loadu_pd(b+i+24));}
    double sum=_mm512_reduce_add_pd(_mm512_add_pd(_mm512_add_pd(s0,s1),_mm512_add_pd(s2,s3)));
    for(;i<n;++i)sum+=b[i];return sum;
}
__attribute__((noinline)) void copy_kernel(double*a,const double*b,size_t n){
    size_t i=0;for(;i+8<=n;i+=8)_mm512_storeu_pd(a+i,_mm512_loadu_pd(b+i));for(;i<n;++i)a[i]=b[i];
}
__attribute__((noinline)) void triad_kernel(double*a,const double*b,const double*c,size_t n){
    const __m512d k=_mm512_set1_pd(3.);size_t i=0;
    for(;i+8<=n;i+=8)_mm512_storeu_pd(a+i,_mm512_fmadd_pd(k,_mm512_loadu_pd(c+i),_mm512_loadu_pd(b+i)));
    for(;i<n;++i)a[i]=b[i]+3.*c[i];
}
#else
#error "Compile on an SVE or AVX512 target with -march=native."
#endif

struct Sample {double start=0,end=0,checksum=0,error=0;int cpu_start=-1,cpu_end=-1;};
struct Worker {int cpu=-1,actual=-1,width=0,vbytes=0,sve=0;std::string error;std::vector<Sample>samples;};
void print_residency(const Residency&r){
    std::cout<<"{\"verified\":"<<(r.verified?"true":"false")<<",\"move_pages_rc\":"<<r.query_rc
      <<",\"move_pages_errno\":"<<r.query_errno<<",\"sampled_pages\":"<<r.samples<<",\"samples_on_target\":"<<r.on_target
      <<",\"numa_maps_verified\":"<<(r.maps_verified?"true":"false")<<",\"numa_maps_line\":"<<quote(r.maps_line)
      <<",\"mapped_pages\":"<<r.mapped_pages<<",\"kernel_page_bytes\":"<<r.kernel_page_bytes<<",\"node_pages\":{";
    bool first=true;for(auto [node,n]:r.node_pages){if(!first)std::cout<<',';first=false;std::cout<<quote(std::to_string(node))<<':'<<n;}
    std::cout<<"}}";
}
int run(std::vector<Entry> entries,size_t array_bytes,int passes,int repeats){
    std::vector<Group>groups;std::map<int,size_t>lookup;
    for(size_t i=0;i<entries.size();++i){auto&e=entries[i];
        if(!lookup.count(e.group)){lookup[e.group]=groups.size();Group g;g.id=e.group;g.node=e.node;groups.push_back(std::move(g));}
        auto&g=groups[lookup.at(e.group)];if(g.node!=e.node)throw std::runtime_error("Group memory_node must be unique");
        e.group_index=lookup.at(e.group);e.local_rank=g.workers.size();g.workers.push_back(i);
    }
    for(auto&g:groups){g.a=std::make_unique<Array>(array_bytes,g.node);g.b=std::make_unique<Array>(array_bytes,g.node);g.c=std::make_unique<Array>(array_bytes,g.node);}
    Barrier barrier(entries.size());std::atomic<bool>failed{false};std::vector<Worker>workers(entries.size());
    std::vector<std::thread>pool;pool.reserve(entries.size());const size_t elements=array_bytes/sizeof(double);
    for(size_t id=0;id<entries.size();++id){auto&w=workers[id];w.cpu=entries[id].cpu;w.samples.resize(3*repeats);
        pool.emplace_back([&,id]{auto&e=entries[id];auto&w=workers[id];auto&g=groups[e.group_index];
            cpu_set_t set;CPU_ZERO(&set);CPU_SET(e.cpu,&set);
            if(sched_setaffinity(0,sizeof(set),&set)){w.error="sched_setaffinity failed";failed=true;}
            CPU_ZERO(&set);if(sched_getaffinity(0,sizeof(set),&set)){w.error="sched_getaffinity failed";failed=true;}
            w.width=CPU_COUNT(&set);w.actual=sched_getcpu();w.vbytes=vector_bytes();w.sve=sve_bytes();
            if(w.width!=1||w.actual!=e.cpu||(w.sve>0&&w.sve!=w.vbytes)){w.error="Affinity/SVE mismatch";failed=true;}
            barrier.wait();if(failed)return;
            const size_t first=elements*size_t(e.local_rank)/g.workers.size(),last=elements*size_t(e.local_rank+1)/g.workers.size();
            const size_t n=last-first;double*a=g.a->data+first;const double*b=g.b->data+first,*c=g.c->data+first;
            for(size_t i=first;i<last;++i){g.a->data[i]=1.;g.b->data[i]=2.;g.c->data[i]=3.;}
            barrier.wait();
            if(id==0){for(auto&group:groups){group.a->before=group.a->query();group.b->before=group.b->query();group.c->before=group.c->query();
                group.a->sdk_before=sdk_verify?sdk_verify(group.a->data,group.a->bytes,0):-2;
                group.b->sdk_before=sdk_verify?sdk_verify(group.b->data,group.b->bytes,0):-2;
                group.c->sdk_before=sdk_verify?sdk_verify(group.c->data,group.c->bytes,0):-2;
                if(!group.a->before.verified||!group.b->before.verified||!group.c->before.verified)failed=true;}}
            barrier.wait();if(failed)return;
            for(int kernel=0;kernel<3;++kernel){
                // One complete warm pass per kernel, outside recorded samples.
                if(kernel==0){volatile double warm=read_kernel(b,n);(void)warm;}
                else if(kernel==1)copy_kernel(a,b,n);else triad_kernel(a,b,c,n);
                barrier.wait();
                for(int r=0;r<repeats;++r){auto&s=w.samples[kernel*repeats+r];double sum=0.;
                    barrier.wait();s.cpu_start=sched_getcpu();s.start=now();
                    for(int p=0;p<passes;++p){
                        // Compiler fence preserves every repeated pass, without adding a team barrier or hardware fence.
                        asm volatile("" ::: "memory");
                        if(kernel==0)sum+=read_kernel(b,n);else if(kernel==1)copy_kernel(a,b,n);else triad_kernel(a,b,c,n);
                        asm volatile("" ::: "memory");
                    }
                    s.end=now();s.cpu_end=sched_getcpu();
                    if(kernel==0){s.checksum=sum;s.error=std::abs(sum-2.*n*passes);}
                    else{const double expected=kernel==1?2.:11.;for(size_t i=0;i<n;++i){
                            if(std::isfinite(a[i])) {
                                s.checksum+=a[i];
                                s.error=std::max(s.error,std::abs(a[i]-expected));
                            } else s.error=std::numeric_limits<double>::max();}}
                    if(s.error!=0||s.cpu_start!=e.cpu||s.cpu_end!=e.cpu){w.error="Checksum/placement verification failed";failed=true;}
                    barrier.wait();
                }
            }
            barrier.wait();
            if(id==0)for(auto&group:groups){group.a->after=group.a->query();group.b->after=group.b->query();group.c->after=group.c->query();
                group.a->sdk_after=sdk_verify?sdk_verify(group.a->data,group.a->bytes,0):-2;
                group.b->sdk_after=sdk_verify?sdk_verify(group.b->data,group.b->bytes,0):-2;
                group.c->sdk_after=sdk_verify?sdk_verify(group.c->data,group.c->bytes,0):-2;
                if(!group.a->after.verified||!group.b->after.verified||!group.c->after.verified)failed=true;}
            barrier.wait();
        });
    }
    for(auto&t:pool)t.join();char hostname[256]{};gethostname(hostname,sizeof(hostname)-1);
    std::cout<<std::setprecision(17)<<"{\"schema\":\"numa-stream-v1\",\"status\":"<<quote(failed?"FAIL":"PASS")
      <<",\"hostname\":"<<quote(hostname)<<",\"isa\":"<<quote(isa)<<",\"compiler\":"<<quote(__VERSION__)
      <<",\"precision\":\"fp64\",\"store_policy\":\"ordinary_temporal_stores\",\"threads\":"<<entries.size()
      <<",\"groups\":"<<groups.size()<<",\"bytes_per_array_per_group\":"<<array_bytes<<",\"passes\":"<<passes<<",\"repeats\":"<<repeats
      <<",\"clock\":\"CLOCK_MONOTONIC_RAW\",\"per_pass_team_barriers\":false,\"placement\":[";
    bool first_group=true;for(auto&g:groups){if(!first_group)std::cout<<',';first_group=false;
        std::cout<<"{\"group\":"<<g.id<<",\"memory_node\":"<<g.node<<",\"arrays\":[";bool first_array=true;
        for(auto item:{std::make_pair("a",g.a.get()),std::make_pair("b",g.b.get()),std::make_pair("c",g.c.get())}){
            if(!first_array)std::cout<<',';first_array=false;auto*a=item.second;
            std::cout<<"{\"name\":"<<quote(item.first)<<",\"bytes\":"<<a->bytes<<",\"address\":"<<quote(std::to_string(reinterpret_cast<uintptr_t>(a->data)))
              <<",\"mbind_rc\":"<<a->mbind_rc<<",\"mbind_errno\":"<<a->mbind_errno<<",\"sdk_verify_before\":"<<a->sdk_before<<",\"sdk_verify_after\":"<<a->sdk_after<<",\"before\":";print_residency(a->before);
            std::cout<<",\"after\":";print_residency(a->after);std::cout<<'}';}
        std::cout<<"]}";}
    std::cout<<"],\"workers\":[";
    for(size_t i=0;i<workers.size();++i){auto&w=workers[i];auto&e=entries[i];if(i)std::cout<<',';
        std::cout<<"{\"cpu\":"<<w.cpu<<",\"actual_cpu\":"<<w.actual<<",\"affinity_width\":"<<w.width<<",\"group\":"<<e.group
          <<",\"memory_node\":"<<e.node<<",\"vector_bytes\":"<<w.vbytes<<",\"sve_vl_bytes\":"<<w.sve<<",\"error\":"<<quote(w.error)<<'}';}
    std::cout<<"],\"kernels\":[";
    for(int k=0;k<3;++k){if(k)std::cout<<',';const char*name=k==0?"read":k==1?"copy":"triad";
        const uint64_t logical=uint64_t(array_bytes)*groups.size()*(k+1)*passes;
        std::cout<<"{\"kernel\":"<<quote(name)<<",\"logical_bytes_per_element\":"<<8*(k+1)<<",\"samples\":[";
        std::vector<double>rates;
        for(int r=0;r<repeats;++r){if(r)std::cout<<',';double start=std::numeric_limits<double>::infinity(),end=0;
            for(auto&w:workers){auto&s=w.samples[k*repeats+r];start=std::min(start,s.start);end=std::max(end,s.end);}
            const double seconds=end-start;const double rate=seconds>0?double(logical)/seconds/1e9:0.;rates.push_back(rate);
            std::cout<<"{\"repeat\":"<<r+1<<",\"seconds\":"<<seconds<<",\"logical_bytes\":"<<logical<<",\"gb_per_second\":"<<rate<<",\"threads\":[";
            for(size_t i=0;i<workers.size();++i){auto&s=workers[i].samples[k*repeats+r];if(i)std::cout<<',';
                std::cout<<"{\"cpu\":"<<workers[i].cpu<<",\"start\":"<<s.start<<",\"end\":"<<s.end<<",\"cpu_start\":"<<s.cpu_start<<",\"cpu_end\":"<<s.cpu_end
                  <<",\"checksum\":"<<s.checksum<<",\"max_abs_error\":"<<s.error<<'}';}std::cout<<"]}";}
        std::sort(rates.begin(),rates.end());double median=rates.size()%2?rates[rates.size()/2]:.5*(rates[rates.size()/2-1]+rates[rates.size()/2]);
        std::cout<<"],\"median_gb_per_second\":"<<median<<",\"max_gb_per_second\":"<<rates.back()<<'}';}
    std::cout<<"]}\n";return failed?1:0;
}
} // namespace
int main(int argc,char**argv){try{
    numa_handle=dlopen("libnuma.so.1",RTLD_NOW|RTLD_LOCAL);
    if(!numa_handle)throw std::runtime_error("Cannot load system libnuma: "+std::string(dlerror()));
    library_mbind=reinterpret_cast<Mbind>(dlsym(numa_handle,"mbind"));
    if(!library_mbind)throw std::runtime_error("System libnuma has no mbind");
    std::string plan,sdk_path;size_t mib=256;int repeats=5,passes=4;
    for(int i=1;i<argc;i+=2){if(i+1>=argc)throw std::runtime_error("Every option requires a value");
        std::string key=argv[i],value=argv[i+1];
        if(key=="--plan")plan=value;else if(key=="--kupl-lib")sdk_path=value;else if(key=="--mib-per-array-per-group")mib=std::stoull(value);
        else if(key=="--passes")passes=std::stoi(value);else if(key=="--repeats")repeats=std::stoi(value);
        else throw std::runtime_error("Unknown option: "+key);}
    if(!sdk_path.empty()){
        sdk_handle=dlopen(sdk_path.c_str(),RTLD_NOW|RTLD_LOCAL);
        if(!sdk_handle)throw std::runtime_error("dlopen KUPL failed: "+std::string(dlerror()));
        sdk_verify=reinterpret_cast<SdkVerify>(dlsym(sdk_handle,"kupl_hbw_verify"));
        if(!sdk_verify)throw std::runtime_error("KUPL library has no kupl_hbw_verify symbol");
    }
    if(plan.empty()||mib<1||mib>65536||passes<1||passes>10000||repeats<1||repeats>30)
        throw std::runtime_error("Usage: bandwidth_bench --plan plan.txt [--kupl-lib /path/libkupl.so] --mib-per-array-per-group 256 --passes 4 --repeats 5");
    const size_t bytes=mib*1024ull*1024;const size_t page=sysconf(_SC_PAGESIZE);
    if(bytes%page)throw std::runtime_error("Array bytes must be page aligned");
    const int rc=run(read_plan(plan),bytes,passes,repeats);if(sdk_handle)dlclose(sdk_handle);return rc;
}catch(const std::exception&e){std::cout<<"{\"schema\":\"numa-stream-v1\",\"status\":\"ERROR\",\"error\":"<<quote(e.what())<<"}\n";return 2;}}
