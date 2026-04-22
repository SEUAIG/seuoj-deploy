#include <cstdio>
#include <queue>
using namespace std;
int main() {
    int n; scanf("%d", &n);
    priority_queue<long long, vector<long long>, greater<>> pq;
    for (int i = 0; i < n; i++) {
        long long x; scanf("%lld", &x);
        pq.push(x);
    }
    long long ans = 0;
    while (pq.size() > 1) {
        long long a = pq.top(); pq.pop();
        long long b = pq.top(); pq.pop();
        ans += a + b;
        pq.push(a + b);
    }
    printf("%lld\n", ans);
}
