#include <cstdio>
int main() {
    int n; long long target;
    scanf("%d%lld", &n, &target);
    long long a[200001];
    for (int i = 1; i <= n; i++) scanf("%lld", &a[i]);
    int l = 1, r = n;
    while (l < r) {
        long long s = a[l] + a[r];
        if (s == target) { printf("%d %d\n", l, r); return 0; }
        else if (s < target) l++;
        else r--;
    }
}
