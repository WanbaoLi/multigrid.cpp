set -e
cd /public2/home/lwb_720/.cache/su-n-cpu-20261111
g++ -O3 -march=native -fopenmp suN_dslash.cpp -o suN_dslash
for n in 3 4 6; do
 for r in 1 2 4 8 12; do ./suN_dslash $n $r 16 6; done
done