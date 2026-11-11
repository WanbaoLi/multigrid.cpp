#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <complex>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>
#include <omp.h>
using Z=std::complex<double>;
using F=std::vector<Z>;
struct Op {
 std::array<int,4> L; int n,r; size_t V; double mass; int bc;
 F gauge; std::vector<size_t> nb; std::vector<double> boundary;
 Op(std::array<int,4> l,int colors,int rhs,double m,int b):L(l),n(colors),r(rhs),V(1),mass(m),bc(b){
  if(n<2||r<1||(bc!=1&&bc!=-1)||!std::isfinite(m))throw std::runtime_error("invalid operator");
  for(int d:L){if(d<2)throw std::runtime_error("extent must be >=2");V*=d;}
  gauge.resize(V*4*n*n);nb.resize(V*8);boundary.assign(V*8,1.);
  for(size_t q=0;q<V;q++)for(int mu=0;mu<4;mu++)for(int pm=0;pm<2;pm++){
   size_t stride=1;for(int d=0;d<mu;d++)stride*=L[d];int coord=(q/stride)%L[mu];
   int step=pm?-1:1,other=(coord+step+L[mu])%L[mu];nb[q*8+2*mu+pm]=size_t((long long)q+(other-coord)*(long long)stride);
   if(mu==3&&((pm&&coord==0)||(!pm&&coord==L[mu]-1)))boundary[q*8+2*mu+pm]=bc;
  }
 }
 size_t ix(size_t q,int s,int c,int k)const{return ((q*4+s)*n+c)*r+k;}
 Z& u(size_t q,int mu,int a,int b){return gauge[((q*4+mu)*n+a)*n+b];}
 Z u(size_t q,int mu,int a,int b)const{return gauge[((q*4+mu)*n+a)*n+b];}
 static void gamma(int mu,int s,int &p,Z &g){
  static const int pair[4][4]={{3,2,1,0},{3,2,1,0},{2,3,0,1},{2,3,0,1}};
  static const Z val[4][4]={{{0,1},{0,1},{0,-1},{0,-1}},{{-1,0},{1,0},{1,0},{-1,0}},{{0,1},{0,-1},{0,-1},{0,1}},{{1,0},{1,0},{1,0},{1,0}}};
  p=pair[mu][s];g=val[mu][s];
 }
 void identity(){std::fill(gauge.begin(),gauge.end(),Z{});for(size_t q=0;q<V;q++)for(int mu=0;mu<4;mu++)for(int c=0;c<n;c++)u(q,mu,c,c)=1.;}
 // Independent QR generation, with determinant corrected to one. Test input,
 // not an equilibrium Monte Carlo ensemble or a substitute for sunw heatbath.
 void random_gauge(unsigned seed){
  std::mt19937_64 rng(seed);std::normal_distribution<double>d;F a(n*n);
  for(size_t q=0;q<V;q++)for(int mu=0;mu<4;mu++){
   for(auto &z:a)z={d(rng),d(rng)};
   for(int j=0;j<n;j++){
    for(int k=0;k<j;k++){Z h=0.;for(int i=0;i<n;i++)h+=std::conj(a[i*n+k])*a[i*n+j];for(int i=0;i<n;i++)a[i*n+j]-=h*a[i*n+k];}
    double norm=0;for(int i=0;i<n;i++)norm+=std::norm(a[i*n+j]);norm=std::sqrt(norm);for(int i=0;i<n;i++)a[i*n+j]/=norm;
   }
   F temp=a;Z det=1.;for(int j=0;j<n;j++){
    int p=j;for(int i=j+1;i<n;i++)if(std::abs(temp[i*n+j])>std::abs(temp[p*n+j]))p=i;
    if(p!=j){for(int k=0;k<n;k++)std::swap(temp[j*n+k],temp[p*n+k]);det=-det;}
    Z diag=temp[j*n+j];det*=diag;for(int i=j+1;i<n;i++){Z f=temp[i*n+j]/diag;for(int k=j+1;k<n;k++)temp[i*n+k]-=f*temp[j*n+k];}
   }
   Z correction=std::conj(det)/std::abs(det);for(int i=0;i<n;i++)a[i*n+n-1]*=correction;
   for(int i=0;i<n;i++)for(int j=0;j<n;j++)u(q,mu,i,j)=a[i*n+j];
  }
 }
 void load(const std::string &path){std::ifstream f(path,std::ios::binary);f.read((char*)gauge.data(),gauge.size()*sizeof(Z));if(!f||f.peek()!=EOF)throw std::runtime_error("gauge file must be [site,mu,row,col] complex128 with exact size");}
 double unitarity()const{double e=0;for(size_t q=0;q<V;q++)for(int mu=0;mu<4;mu++)for(int i=0;i<n;i++)for(int j=0;j<n;j++){Z z=0.;for(int k=0;k<n;k++)z+=std::conj(u(q,mu,k,i))*u(q,mu,k,j);e=std::max(e,std::abs(z-Z(i==j)));}return e;}
 // Independent full-spin scalar stencil. Global operator is mass-normalized
 // Wilson: (4+mass)*psi - 1/2 sum[(1-gamma)U psi+ +(1+gamma)Udag psi-].
 void reference(const F &x,F &y)const{
  y.resize(x.size());
#pragma omp parallel for schedule(static)
  for(size_t q=0;q<V;q++)for(int s=0;s<4;s++)for(int c=0;c<n;c++)for(int k=0;k<r;k++){
   Z z=(4+mass)*x[ix(q,s,c,k)];
   for(int mu=0;mu<4;mu++){int p;Z g;gamma(mu,s,p,g);size_t qp=nb[q*8+2*mu],qm=nb[q*8+2*mu+1];
    for(int j=0;j<n;j++)z-=.5*(boundary[q*8+2*mu]*u(q,mu,c,j)*(x[ix(qp,s,j,k)]-g*x[ix(qp,p,j,k)])+boundary[q*8+2*mu+1]*std::conj(u(qm,mu,j,c))*(x[ix(qm,s,j,k)]+g*x[ix(qm,p,j,k)]));
   }y[ix(q,s,c,k)]=z;
  }
 }
 // Paper's two projected N x R matrices. RHS is contiguous; AVX512 can
 // vectorize over RHS. One SU(N) coefficient is reused for all RHS lanes.
 void fused(const F &x,F &y)const{
  y.resize(x.size());
#pragma omp parallel
  {
   F projected(2*n*r),result(2*n*r);
#pragma omp for schedule(static)
   for(size_t q=0;q<V;q++){
    for(int s=0;s<4;s++)for(int c=0;c<n;c++)for(int k=0;k<r;k++)y[ix(q,s,c,k)]=(4+mass)*x[ix(q,s,c,k)];
    for(int mu=0;mu<4;mu++)for(int pm=0;pm<2;pm++){
     size_t qn=nb[q*8+2*mu+pm];double sign=pm?1.:-1.,weight=-.5*boundary[q*8+2*mu+pm];
     for(int s=0;s<2;s++){int p;Z g;gamma(mu,s,p,g);for(int j=0;j<n;j++)for(int k=0;k<r;k++)projected[(s*n+j)*r+k]=x[ix(qn,s,j,k)]+sign*g*x[ix(qn,p,j,k)];}
     std::fill(result.begin(),result.end(),Z{});
     for(int s=0;s<2;s++)for(int c=0;c<n;c++)for(int j=0;j<n;j++){
      Z a=pm?std::conj(u(qn,mu,j,c)):u(q,mu,c,j);
#pragma omp simd
      for(int k=0;k<r;k++)result[(s*n+c)*r+k]+=a*projected[(s*n+j)*r+k];
     }
     for(int s=0;s<2;s++){int p;Z g;gamma(mu,s,p,g);int unused;Z gp;gamma(mu,p,unused,gp);
      for(int c=0;c<n;c++)for(int k=0;k<r;k++){Z v=weight*result[(s*n+c)*r+k];y[ix(q,s,c,k)]+=v;y[ix(q,p,c,k)]+=sign*gp*v;}
     }
    }
   }
  }
 }
};
double norm2(const F&a){double v=0;
#pragma omp parallel for reduction(+:v) schedule(static) if(a.size()>8192)
 for(size_t i=0;i<a.size();i++)v+=std::norm(a[i]);return v;}
double error(const F&a,const F&b){double d=0;for(size_t i=0;i<a.size();i++)d+=std::norm(a[i]-b[i]);return std::sqrt(d/std::max(norm2(b),1e-300));}
Z dot(const F&a,const F&b){double re=0,im=0;
#pragma omp parallel for reduction(+:re,im) schedule(static) if(a.size()>8192)
 for(size_t i=0;i<a.size();i++){Z z=std::conj(a[i])*b[i];re+=z.real();im+=z.imag();}return {re,im};}
// Global/merged BiCGStab, as discussed in section 4.5 of the paper.
// A final explicit true residual is checked separately for every RHS.
int solve(const Op&o,const F&b,F&x,double tol,int maxiter,std::vector<double>&res){
 size_t n=b.size();x.assign(n,0.);F rr=b,shadow=b,p(n),v(n),s(n),t(n),ax;
 // A deterministic perturbed shadow prevents exact BiCGStab breakdown for
 // point-source columns whose residuals can become orthogonal to b. It does
 // not change the true residual gate, which is always evaluated with M*x.
 for(size_t i=0;i<n;i++)shadow[i]+=1e-3*Z(std::sin(.017*i),std::cos(.013*i))*(1.+std::abs(b[i]));
 Z rho0=1.,alpha=1.,omega=1.;double bn=std::sqrt(norm2(b));int it;
 for(it=0;it<maxiter;it++){
  Z rho=dot(shadow,rr);if(std::abs(rho)<1e-290)throw std::runtime_error("BiCGStab rho breakdown");Z beta=(rho/rho0)*(alpha/omega);
  #pragma omp parallel for schedule(static) if(n>8192)
  for(size_t k=0;k<n;k++)p[k]=rr[k]+beta*(p[k]-omega*v[k]);o.fused(p,v);Z den=dot(shadow,v);if(std::abs(den)<1e-290)throw std::runtime_error("BiCGStab alpha breakdown");alpha=rho/den;
  #pragma omp parallel for schedule(static) if(n>8192)
  for(size_t k=0;k<n;k++)s[k]=rr[k]-alpha*v[k];
  if(std::sqrt(norm2(s))<tol*bn){
   #pragma omp parallel for schedule(static) if(n>8192)
   for(size_t k=0;k<n;k++)x[k]+=alpha*p[k];++it;break;}
  o.fused(s,t);double tt=norm2(t);if(tt<1e-290)throw std::runtime_error("BiCGStab omega breakdown");omega=dot(t,s)/tt;
  if(std::abs(omega)<1e-290)throw std::runtime_error("BiCGStab zero omega");
  #pragma omp parallel for schedule(static) if(n>8192)
  for(size_t k=0;k<n;k++){x[k]+=alpha*p[k]+omega*s[k];rr[k]=s[k]-omega*t[k];}
  if(std::sqrt(norm2(rr))<tol*bn){++it;break;}rho0=rho;
 }
 o.reference(x,ax);res.assign(o.r,0.);std::vector<double>nr(o.r),dr(o.r);for(size_t k=0;k<n;k++){nr[k%o.r]+=std::norm(b[k]-ax[k]);dr[k%o.r]+=std::norm(b[k]);}
 for(int k=0;k<o.r;k++){res[k]=std::sqrt(nr[k]/std::max(dr[k],1e-300));if(res[k]>1e-8)throw std::runtime_error("per-RHS true residual exceeds 1e-8");}return it;
}
int solve_independent_columns(const Op&o,const F&b,F&x,double tol,int maxiter,std::vector<double>&res){
 if(o.r<1)throw std::runtime_error("invalid RHS count");x.assign(b.size(),Z{});res.assign(o.r,0.);int max_it=0;
 Op one(o.L,o.n,1,o.mass,o.bc);one.gauge=o.gauge;
 for(int k=0;k<o.r;k++){
  F bk(one.V*4*one.n),xk;for(size_t i=0;i<bk.size();i++)bk[i]=b[i*o.r+k];std::vector<double>rk;int it=solve(one,bk,xk,tol,maxiter,rk);max_it=std::max(max_it,it);res[k]=rk[0];
  for(size_t i=0;i<xk.size();i++)x[i*o.r+k]=xk[i];
 }
 return max_it;
}
F input(const Op&o){F x(o.V*4*o.n*o.r);std::mt19937_64 g(44);std::normal_distribution<double>d;for(Z&z:x)z={d(g),d(g)};return x;}
void self_test(){
 for(int n:{2,3,4,6,8})for(int r:{1,3,12})for(int bc:{1,-1}){
  Op o({4,4,4,4},n,r,.5,bc);o.identity();F x(input(o)),a,b;o.reference(x,a);o.fused(x,b);if(error(b,a)>2e-14)throw std::runtime_error("identity stencil mismatch");
  // Independent exact plane-wave eigenmode, with all spin/color amplitudes 1.
  std::array<double,4> p={2*std::acos(-1.)/4,0.,0.,bc<0?std::acos(-1.)/4:0.};
  for(size_t q=0;q<o.V;q++){size_t qq=q;double angle=0;for(int mu=0;mu<4;mu++){angle+=p[mu]*(qq%4);qq/=4;}for(int s=0;s<4;s++)for(int c=0;c<n;c++)for(int k=0;k<r;k++)x[o.ix(q,s,c,k)]=std::polar(double(k+1),angle);}
  o.fused(x,b);F exact(x.size());double real=4+o.mass;for(double v:p)real-=std::cos(v);
  for(size_t q=0;q<o.V;q++)for(int s=0;s<4;s++)for(int c=0;c<n;c++)for(int k=0;k<r;k++){Z z=real*x[o.ix(q,s,c,k)];for(int mu=0;mu<4;mu++){int paired;Z g;Op::gamma(mu,s,paired,g);z+=Z(0,std::sin(p[mu]))*g*x[o.ix(q,paired,c,k)];}exact[o.ix(q,s,c,k)]=z;}
  if(error(b,exact)>2e-14)throw std::runtime_error("plane wave/normalization/boundary mismatch");
  o.random_gauge(11);if(o.unitarity()>2e-12)throw std::runtime_error("SU(N) unitarity");x=input(o);o.reference(x,a);o.fused(x,b);if(error(b,a)>2e-14)throw std::runtime_error("random SU(N) stencil mismatch");
  Op one(o.L,n,1,o.mass,bc);one.gauge=o.gauge;for(int k=0;k<r;k++){F v(o.V*4*n),w;for(size_t i=0;i<v.size();i++)v[i]=x[i*r+k];one.reference(v,w);for(size_t i=0;i<w.size();i++)if(std::abs(w[i]-a[i*r+k])>2e-13)throw std::runtime_error("RHS independence");}
  o.identity();o.reference(x,a);F solution;std::vector<double>res;int it=solve(o,a,solution,1e-11,500,res);if(error(solution,x)>1e-9)throw std::runtime_error("merged solve exact solution");
 }
 std::cout<<"PASS 30 cases: N2/3/4/6/8, R1/3/12, periodic/AP time, full-spin oracle, analytic plane wave, random SU(N), RHS independence, merged solve\n";
}
int main(int argc,char**argv){try{
 omp_set_dynamic(0);if(argc==2&&std::string(argv[1])=="--self-test"){omp_set_num_threads(4);self_test();return 0;}
 if(argc<9)throw std::runtime_error("sun_cpu N RHS threads repeats Lx Ly Lz Lt [gauge.bin|identity|random] [operator|solve|propagator] [mass] [output-prefix]");
 int n=std::stoi(argv[1]),r=std::stoi(argv[2]),threads=std::stoi(argv[3]),reps=std::stoi(argv[4]);if(threads<1||reps<2)throw std::runtime_error("threads>=1 repeats>=2");omp_set_num_threads(threads);
 Op o({std::stoi(argv[5]),std::stoi(argv[6]),std::stoi(argv[7]),std::stoi(argv[8])},n,r,argc>11?std::stod(argv[11]):.5,-1);
 std::string data=argc>9?argv[9]:"random",mode=argc>10?argv[10]:"operator";
 if(data=="identity")o.identity();else if(data=="random")o.random_gauge(11);else o.load(data);
 F x=input(o),a,b;o.reference(x,a);o.fused(x,b);double e=error(b,a);if(e>2e-13)throw std::runtime_error("operator oracle gate");
 if(mode=="propagator"){if(r!=4*n)throw std::runtime_error("complete source requires RHS=4*N");a.assign(x.size(),0.);for(int k=0;k<r;k++)a[o.ix(0,k/n,k%n,k)]=1.;}
 std::vector<double>times;using clock=std::chrono::steady_clock;int its=0;std::vector<double>res;
 for(int i=0;i<reps;i++){auto start=clock::now();if(mode=="operator")o.fused(x,b);else if(mode=="solve")its=solve(o,a,b,1e-10,2000,res);else if(mode=="propagator")its=solve_independent_columns(o,a,b,1e-10,2000,res);else throw std::runtime_error("unknown mode");double seconds=std::chrono::duration<double>(clock::now()-start).count();times.push_back(seconds);}
 if(argc>12){F column(b.size()/r);for(int k=0;k<r;k++){
  #pragma omp parallel for schedule(static)
  for(size_t i=0;i<column.size();i++)column[i]=b[i*r+k];
  std::ofstream f(std::string(argv[12])+"-column"+std::to_string(k)+".bin",std::ios::binary);if(!f)throw std::runtime_error("cannot open output");f.write((const char*)column.data(),column.size()*sizeof(Z));if(!f)throw std::runtime_error("output write failed");}}
 std::cout<<std::setprecision(12)<<"{\"N\":"<<n<<",\"rhs\":"<<r<<",\"threads\":"<<threads<<",\"volume\":"<<o.V<<",\"mass\":"<<o.mass<<",\"time_boundary\":-1,\"input\":\""<<data<<"\",\"mode\":\""<<mode<<"\",\"operator_relative_error\":"<<e<<",\"iterations\":"<<its<<",\"seconds\":[";
 for(size_t i=0;i<times.size();i++)std::cout<<(i?",":"")<<times[i];std::cout<<"],\"per_rhs_residual\":[";for(size_t k=0;k<res.size();k++)std::cout<<(k?",":"")<<res[k];std::cout<<"]}\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
