#include <cstdio>
#include <cstring>
#include <algorithm>
using namespace std;
int main() {
    char s[100002];
    scanf("%s", s);
    int n = strlen(s);
    int cnt[26] = {};
    for (int i = 0; i < n; i++) cnt[s[i] - 'a']++;
    int odd = 0;
    char mid_ch = 0;
    for (int i = 0; i < 26; i++) {
        if (cnt[i] % 2) { odd++; mid_ch = 'a' + i; }
    }
    if (odd > 1) { puts("impossible"); return 0; }
    char left[50001];
    int pos = 0;
    for (int i = 0; i < 26; i++)
        for (int j = 0; j < cnt[i] / 2; j++)
            left[pos++] = 'a' + i;
    for (int i = 0; i < pos; i++) putchar(left[i]);
    if (odd) putchar(mid_ch);
    for (int i = pos - 1; i >= 0; i--) putchar(left[i]);
    putchar('\n');
}
