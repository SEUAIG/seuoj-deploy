#include <cstdio>
#include <queue>
using namespace std;
char grid[1001][1002];
int dist[1001][1001];
int dx[] = {0, 0, 1, -1}, dy[] = {1, -1, 0, 0};
int main() {
    int n, m;
    scanf("%d%d", &n, &m);
    for (int i = 0; i < n; i++) scanf("%s", grid[i]);
    if (grid[0][0] == '#' || grid[n-1][m-1] == '#') { puts("-1"); return 0; }
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++) dist[i][j] = -1;
    queue<pair<int,int>> q;
    q.push({0, 0}); dist[0][0] = 0;
    while (!q.empty()) {
        auto [x, y] = q.front(); q.pop();
        for (int d = 0; d < 4; d++) {
            int nx = x + dx[d], ny = y + dy[d];
            if (nx >= 0 && nx < n && ny >= 0 && ny < m &&
                grid[nx][ny] == '.' && dist[nx][ny] == -1) {
                dist[nx][ny] = dist[x][y] + 1;
                q.push({nx, ny});
            }
        }
    }
    printf("%d\n", dist[n-1][m-1]);
}
