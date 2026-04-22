#include "testlib.h"
#include <vector>
int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);
    int n = inf.readInt();
    long long target = inf.readLong();
    std::vector<long long> a(n + 1);
    for (int i = 1; i <= n; i++) a[i] = inf.readLong();
    int pi = ouf.readInt(), pj = ouf.readInt();
    if (pi < 1 || pi > n || pj < 1 || pj > n)
        quitf(_wa, "Index out of range: %d %d", pi, pj);
    if (pi >= pj)
        quitf(_wa, "Need i < j, got %d %d", pi, pj);
    if (a[pi] + a[pj] != target)
        quitf(_wa, "a[%d]+a[%d]=%lld, expected %lld", pi, pj, a[pi] + a[pj], target);
    quitf(_ok, "");
}
