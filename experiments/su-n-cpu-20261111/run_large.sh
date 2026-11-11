set -e
cd /public2/home/lwb_720/.cache/su-n-cpu-20261111
g++ -O3 -march=native -fopenmp suN_dslash.cpp -o suN_dslash
./suN_dslash 3 12 16 5 16 16 16 32
./suN_dslash 3 12 16 4 24 24 24 64
./suN_dslash 4 12 16 5 16 16 16 32
./suN_dslash 6 12 16 5 16 16 16 32