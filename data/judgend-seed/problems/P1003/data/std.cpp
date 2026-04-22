#include <cstdio>
#include <algorithm>
using namespace std;
int main() {
    char s[200002];
    scanf("%s", s);
    int depth = 0, maxd = 0;
    for (int i = 0; s[i]; i++) {
        if (s[i] == '(') { depth++; maxd = max(maxd, depth); }
        else { depth--; if (depth < 0) { puts("-1"); return 0; } }
    }
    printf("%d\n", depth == 0 ? maxd : -1);
}
