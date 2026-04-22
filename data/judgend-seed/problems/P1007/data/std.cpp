#include <cstdio>
#include <vector>
using namespace std;
long long cnt;
void merge_sort(vector<int>& a, int l, int r) {
    if (r - l <= 1) return;
    int m = (l + r) / 2;
    merge_sort(a, l, m);
    merge_sort(a, m, r);
    vector<int> tmp;
    int i = l, j = m;
    while (i < m && j < r) {
        if (a[i] <= a[j]) tmp.push_back(a[i++]);
        else { tmp.push_back(a[j++]); cnt += m - i; }
    }
    while (i < m) tmp.push_back(a[i++]);
    while (j < r) tmp.push_back(a[j++]);
    for (int k = l; k < r; k++) a[k] = tmp[k - l];
}
int main() {
    int n; scanf("%d", &n);
    vector<int> a(n);
    for (int i = 0; i < n; i++) scanf("%d", &a[i]);
    cnt = 0;
    merge_sort(a, 0, n);
    printf("%lld\n", cnt);
}
