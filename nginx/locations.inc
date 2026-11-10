# 共享 location 配置，由 core-tls.conf 的 HTTP / HTTPS 两个 server 块 include
location / {
    root /usr/share/nginx/html;
    index index.html;
    add_header Cache-Control "no-cache";
    try_files $uri $uri/ /index.html;
}

location /assets/ {
    root /usr/share/nginx/html;
    try_files $uri =404;
    add_header Cache-Control "public, max-age=31536000, immutable";
}

location /api/ {
    proxy_pass http://backend:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 60s;
    proxy_send_timeout 60s;
    client_max_body_size 50M;
}

location /internal/judgend/ {
    internal;
    proxy_pass http://judgend:9090/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
