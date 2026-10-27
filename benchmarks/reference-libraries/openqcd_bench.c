#define MAIN_PROGRAM
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <mpi.h>
#include <omp.h>
#include "su3.h"
#include "flags.h"
#include "utils.h"
#include "lattice.h"
#include "uflds.h"
#include "sflds.h"
#include "linalg.h"
#include "lqcd/core/dirac.h"
#include "dfl.h"
#include "random.h"
#include "sw_term.h"
#include "global.h"

static size_t site(int t,int z,int y,int x) { return (((size_t)t*24+z)*24+y)*24+x; }
static void read_file(const char *dir,const char *name,void *p,size_t n,size_t offset) {
    char file[4096];FILE *f;
    snprintf(file,sizeof(file),"%s/%s",dir,name);f=fopen(file,"rb");
    if(!f || fseeko(f,(off_t)offset,SEEK_SET) || fread(p,1,n,f)!=n)MPI_Abort(MPI_COMM_WORLD,2);
    fclose(f);
}
static void load_spinor(const char *dir,const char *name,spinor_dble *s) {
    spinor_dble *tmp=malloc(VOLUME*sizeof(*tmp));int j;
    read_file(dir,name,tmp,VOLUME*sizeof(*tmp),(size_t)cpr[0]*VOLUME*sizeof(*tmp));
    for(j=0;j<VOLUME;j++)s[ipt[j]]=tmp[j];
    free(tmp);
}
static double relative(const spinor_dble *a,const spinor_dble *b) {
    const double *x=(const double*)a,*y=(const double*)b;double e=0,n=0,v[2],r[2];int j;
    #pragma omp parallel for reduction(+:e,n)
    for(j=0;j<24*VOLUME;j++){e+=(x[j]-y[j])*(x[j]-y[j]);n+=y[j]*y[j];}
    v[0]=e;v[1]=n;MPI_Allreduce(v,r,2,MPI_DOUBLE,MPI_SUM,MPI_COMM_WORLD);return sqrt(r[0]/r[1]);
}
int main(int argc,char **argv) {
    int rank,size,t,z,y,x,mu,j,idx,coord[4],back[4],bs[4]={4,4,4,4},status[3],ifail;
    const int dims[4]={64,24,24,24};
    double kappa=1/(2*(4-.277)),phi[2]={0,0},theta[3]={0,0,0},tm[2],res[2],setup,err;
    int its[2];FILE *f;char file[4096];su3_dble *u,*g;spinor_dble **s,*tmp;
    mpi_init(argc,argv);MPI_Comm_rank(MPI_COMM_WORLD,&rank);MPI_Comm_size(MPI_COMM_WORLD,&size);
    if(argc<3 || size!=NPROC)MPI_Abort(MPI_COMM_WORLD,2);
    set_lat_parms(6.2,1.,1,&kappa,0,1.);set_bc_parms(3,1.,1.,1.,1.,phi,phi,theta);
    set_sap_parms(bs,1,4,5);set_dfl_parms(bs,24);
    set_dfl_gen_parms(kappa,0.,6,4,5);set_dfl_pro_parms(16,64,.01,24,.1);
    start_ranlux(0,20261014);geometry();set_sw_parms(-.277);set_tm_parms(0);
    g=malloc((size_t)64*24*24*24*4*sizeof(*g));
    read_file(argv[1],"gauge.bin",g,(size_t)64*24*24*24*4*sizeof(*g),0);
    u=udfld();
    for(t=0;t<L0;t++)for(z=0;z<L1;z++)for(y=0;y<L2;y++)for(x=0;x<L3;x++) {
        j=((t*L1+z)*L2+y)*L3+x;idx=ipt[j];if(idx<VOLUME/2)continue;
        coord[0]=cpr[0]*L0+t;coord[1]=z;coord[2]=y;coord[3]=x;
        for(mu=0;mu<4;mu++) {
            memcpy(back,coord,sizeof(back));back[mu]=(back[mu]+dims[mu]-1)%dims[mu];
            u[8*(idx-VOLUME/2)+2*mu]=g[4*site(coord[0],z,y,x)+3-mu];
            u[8*(idx-VOLUME/2)+2*mu+1]=g[4*site(back[0],back[1],back[2],back[3])+3-mu];
        }
    }
    free(g);set_flags(UPDATED_UD);set_ud_phase();sw_term(NO_PTS);
    alloc_ws(64);alloc_wsd(8);alloc_wv(64);alloc_wvd(40);s=reserve_wsd(4);
    load_spinor(argv[1],"probe_openqcd.bin",s[0]);load_spinor(argv[1],"D_probe_openqcd.bin",s[2]);
    Dw_dble(0.,s[0],s[1]);err=relative(s[1],s[2]);
    if(!rank){printf("OPERATOR_ERROR %.17g\n",err);fflush(stdout);}
    if(!isfinite(err)||err>1e-11)MPI_Abort(MPI_COMM_WORLD,3);
    if(argc>3 && !strcmp(argv[3],"probe")){MPI_Finalize();return 0;}
    MPI_Barrier(MPI_COMM_WORLD);setup=MPI_Wtime();dfl_modes(&ifail,status);setup=MPI_Wtime()-setup;
    if(!rank){printf("SETUP %.9g status %d %d %d\n",setup,ifail,status[0],status[1]);fflush(stdout);}
    if(ifail<0)MPI_Abort(MPI_COMM_WORLD,4);
    load_spinor(argv[1],"b_openqcd.bin",s[0]);
    for(j=0;j<2;j++) {
        set_sd2zero(VOLUME_TRD,2,s[1]);MPI_Barrier(MPI_COMM_WORLD);tm[j]=MPI_Wtime();
        dfl_sap_gcr(24,1000,0,1e-8,0.,s[0],s[1],&ifail,status);
        tm[j]=MPI_Wtime()-tm[j];its[j]=status[0];
        double tmax;MPI_Allreduce(&tm[j],&tmax,1,MPI_DOUBLE,MPI_MAX,MPI_COMM_WORLD);tm[j]=tmax;
        Dw_dble(0.,s[1],s[2]);res[j]=relative(s[2],s[0]);
        if(!rank){printf("SOLVE %d seconds %.9g iterations %d residual %.17g ifail %d\n",j+1,tm[j],its[j],res[j],ifail);fflush(stdout);}
        if(ifail<0 || !isfinite(res[j]) || res[j]>1e-8)MPI_Abort(MPI_COMM_WORLD,5);
    }
    tmp=malloc(VOLUME*sizeof(*tmp));for(j=0;j<VOLUME;j++)tmp[j]=s[1][ipt[j]];
    snprintf(file,sizeof(file),"%s.rank%d.bin",argv[2],cpr[0]);f=fopen(file,"wb");fwrite(tmp,sizeof(*tmp),VOLUME,f);fclose(f);free(tmp);
    if(!rank){snprintf(file,sizeof(file),"%s.json",argv[2]);f=fopen(file,"w");fprintf(f,
      "{\"library\":\"openQCD\",\"ranks\":%d,\"threads_per_rank\":%d,\"setup_seconds\":%.17g,\"operator_error\":%.17g,\"solve_seconds\":[%.17g,%.17g],\"iterations\":[%d,%d],\"true_residual\":[%.17g,%.17g]}\n",size,NTHREAD,setup,err,tm[0],tm[1],its[0],its[1],res[0],res[1]);fclose(f);}
    MPI_Finalize();return 0;
}
