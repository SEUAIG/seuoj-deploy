#include <cstdio>
#include <algorithm>
using namespace std;
int main() {
    int n; long long k;
    scanf("%d%lld", &n, &k);
    long long a[100001], hi = 0;
    for (int i = 0; i < n; i++) {
        scanf("%lld", &a[i]);
        hi = max(hi, a[i]);
    }
    long long lo = 0;
    while (lo < hi) {
        long long mid = lo + (hi - lo + 1) / 2;
        long long cnt = 0;
        for (int i = 0; i < n; i++) cnt += a[i] / mid;
        if (cnt >= k) lo = mid;
        else hi = mid - 1;
    }
    printf("%lld\n", lo);
}
