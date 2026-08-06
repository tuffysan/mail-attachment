#!/usr/bin/env bash
set -Eeuo pipefail
required=(
  frontend/package.json
  frontend/Dockerfile
  frontend/nginx.conf
  frontend/index.html
  frontend/src/main.tsx
  frontend/src/App.tsx
  frontend/src/api.ts
  frontend/src/pages/LoginPage.tsx
  frontend/src/pages/DashboardPage.tsx
)
for file in "${required[@]}"; do
  [[ -f "$file" ]] || { echo "Missing frontend file: $file" >&2; exit 1; }
done
grep -q '"react"' frontend/package.json
grep -q 'proxy_pass http://backend:8080' frontend/nginx.conf
grep -q 'frontend:' compose.yml
grep -q 'FRONTEND_PORT' .env.example
echo "Frontend static checks passed."
