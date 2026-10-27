#include <mpi.h>
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "DDalphaAMG.h"

static int lt;
static int gauge_index(int t,int z,int y,int x,int mu) {
    return (((t*24+z)*24+y)*24+x)*72+(3-mu)*18;
}
static void load(const char *dir,const char *name,double *p,size_t n,size_t offset) {
    char file[4096]; FILE *f;
    snprintf(file,sizeof(file),"%s/%s",dir,name);f=fopen(file,"rb");
    if(!f || fseeko(f,(off_t)(offset*sizeof(double)),SEEK_SET) || fread(p,sizeof(double),n,f)!=n) {
        fprintf(stderr,"Cannot read %s\n",file);MPI_Abort(MPI_COMM_WORLD,2);
    }
    fclose(f);
}
static double rel(const double *a,const double *b,size_t n) {
    double d=0,s=0,v[2],g[2];size_t j;
    #pragma omp parallel for reduction(+:d,s)
    for(j=0;j<n;j++){d+=(a[j]-b[j])*(a[j]-b[j]);s+=b[j]*b[j];}
    v[0]=d;v[1]=s;MPI_Allreduce(v,g,2,MPI_DOUBLE,MPI_SUM,MPI_COMM_WORLD);
    return sqrt(g[0]/g[1]);
}
int main(int argc,char **argv) {
    int rank,size,provided,coords[4],r,j,levels=argc>3?atoi(argv[3]):3;
    DDalphaAMG_init init={0};DDalphaAMG_parameters p;DDalphaAMG_status st;
    double *gauge,*b,*x,*probe,*expected,*image,setup,tm[2],res[2],operr;
    int iterations[2];size_t V,n;char file[4096];FILE *f;
    MPI_Init_thread(&argc,&argv,MPI_THREAD_FUNNELED,&provided);
    MPI_Comm_rank(MPI_COMM_WORLD,&rank);MPI_Comm_size(MPI_COMM_WORLD,&size);
    if(argc<3 || 64%size)MPI_Abort(MPI_COMM_WORLD,2);
    lt=64/size;V=(size_t)lt*24*24*24;n=24*V;
    init.comm_cart=MPI_COMM_WORLD;
    init.global_lattice[0]=64;init.global_lattice[1]=init.global_lattice[2]=init.global_lattice[3]=24;
    init.procs[0]=size;init.procs[1]=init.procs[2]=init.procs[3]=1;
    init.block_lattice[0]=4;init.block_lattice[1]=init.block_lattice[2]=init.block_lattice[3]=6;
    init.bc=1;init.kappa=1/(2*(4-.277));init.csw=1;init.mu=0;
    init.number_of_levels=levels;init.number_openmp_threads=omp_get_max_threads();
    unsigned int seeds[size];for(j=0;j<size;j++)seeds[j]=20261014+j;
    init.rnd_seeds=seeds;
    DDalphaAMG_initialize(&init,&p,&st);
    p.conf_index_fct=gauge_index;p.print=0;
    DDalphaAMG_update_parameters(&p,&st);
    MPI_Comm cart=DDalphaAMG_get_communicator();MPI_Comm_rank(cart,&r);MPI_Cart_coords(cart,r,4,coords);
    gauge=malloc(72*V*sizeof(double));b=malloc(n*sizeof(double));x=calloc(n,sizeof(double));
    probe=malloc(n*sizeof(double));expected=malloc(n*sizeof(double));image=malloc(n*sizeof(double));
    load(argv[1],"gauge.bin",gauge,72*V,coords[0]*72*V);
    load(argv[1],"b_openqcd.bin",b,n,coords[0]*n);
    load(argv[1],"probe_openqcd.bin",probe,n,coords[0]*n);
    load(argv[1],"D_probe_openqcd.bin",expected,n,coords[0]*n);
    DDalphaAMG_set_configuration(gauge,&st);
    MPI_Barrier(MPI_COMM_WORLD);setup=MPI_Wtime();DDalphaAMG_setup(&st);
    setup=MPI_Wtime()-setup;
    DDalphaAMG_apply_operator(image,probe,&st);operr=rel(image,expected,n);
    if(!rank){printf("OPERATOR_ERROR %.17g\n",operr);fflush(stdout);}
    if(operr>1e-11 || !isfinite(operr))MPI_Abort(MPI_COMM_WORLD,3);
    if(!rank){printf("SETUP_SECONDS %.9g\n",setup);fflush(stdout);}
    for(j=0;j<2;j++) {
        memset(x,0,n*sizeof(double));MPI_Barrier(MPI_COMM_WORLD);
        tm[j]=MPI_Wtime();DDalphaAMG_solve(x,b,1e-8,&st);tm[j]=MPI_Wtime()-tm[j];
        iterations[j]=st.iter_count;
        double tmax;MPI_Allreduce(&tm[j],&tmax,1,MPI_DOUBLE,MPI_MAX,MPI_COMM_WORLD);tm[j]=tmax;
        DDalphaAMG_apply_operator(image,x,&st);res[j]=rel(image,b,n);
        if(!rank){printf("SOLVE %d seconds %.9g iterations %d residual %.17g\n",j+1,tm[j],iterations[j],res[j]);fflush(stdout);}
        if(!isfinite(res[j]) || res[j]>1e-8)MPI_Abort(MPI_COMM_WORLD,4);
    }
    snprintf(file,sizeof(file),"%s.rank%d.bin",argv[2],coords[0]);f=fopen(file,"wb");
    fwrite(x,sizeof(double),n,f);fclose(f);
    if(!rank){snprintf(file,sizeof(file),"%s.json",argv[2]);f=fopen(file,"w");
      fprintf(f,"{\"library\":\"DDalphaAMG\",\"ranks\":%d,\"threads_per_rank\":%d,\"levels\":%d,\"setup_seconds\":%.17g,\"operator_error\":%.17g,\"solve_seconds\":[%.17g,%.17g],\"iterations\":[%d,%d],\"true_residual\":[%.17g,%.17g]}\n",size,init.number_openmp_threads,levels,setup,operr,tm[0],tm[1],iterations[0],iterations[1],res[0],res[1]);fclose(f);}
    DDalphaAMG_finalize();free(gauge);free(b);free(x);free(probe);free(expected);free(image);MPI_Finalize();return 0;
}
