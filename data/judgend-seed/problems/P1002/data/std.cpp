#include <cstdio>
#include <algorithm>
using namespace std;
int main() {
    int n; scanf("%d", &n);
    long long cur, best;
    long long x; scanf("%lld", &x);
    cur = best = x;
    for (int i = 1; i < n; i++) {
        scanf("%lld", &x);
        cur = max(x, cur + x);
        best = max(best, cur);
    }
    printf("%lld\n", best);
}
