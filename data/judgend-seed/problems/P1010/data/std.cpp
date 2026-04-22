#include <cstdio>
#include <queue>
using namespace std;
int n, m;
char grid[1001][1002];
int dx[] = {0, 0, 1, -1}, dy[] = {1, -1, 0, 0};
void bfs(int sx, int sy) {
    queue<pair<int,int>> q;
    q.push({sx, sy}); grid[sx][sy] = '0';
    while (!q.empty()) {
        auto [x, y] = q.front(); q.pop();
        for (int d = 0; d < 4; d++) {
            int nx = x + dx[d], ny = y + dy[d];
            if (nx >= 0 && nx < n && ny >= 0 && ny < m && grid[nx][ny] == '1') {
                grid[nx][ny] = '0';
                q.push({nx, ny});
            }
        }
    }
}
int main() {
    scanf("%d%d", &n, &m);
    for (int i = 0; i < n; i++) scanf("%s", grid[i]);
    int ans = 0;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++)
            if (grid[i][j] == '1') { bfs(i, j); ans++; }
    printf("%d\n", ans);
}
