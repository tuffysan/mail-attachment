#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/mail-attachment-hub}"
COMPOSE=(-f compose.yml -f compose.override.lxc.yml)

[[ $EUID -eq 0 ]] || {
  echo "Kör som root inne i LXC:n."
  exit 1
}

cd "$APP_DIR"

command -v docker >/dev/null 2>&1 || {
  echo "docker saknas." >&2
  exit 1
}
docker compose version >/dev/null 2>&1 || {
  echo "docker compose saknas." >&2
  exit 1
}

echo "============================================================"
echo " Mail Attachment Hub - Storage Self Test"
echo "============================================================"

echo
echo "[1/4] Kör storage-init..."
docker compose \
  --env-file .env \
  "${COMPOSE[@]}" \
  run --rm --no-deps storage-init

test_container_storage() {
  local service="$1"

  echo
  echo "Testing ${service}..."

  docker compose \
    --env-file .env \
    "${COMPOSE[@]}" \
    exec -T "$service" sh -ec '
      echo "Identity:"
      id

      for dir in /data/attachments /data/routed; do
        echo
        echo "Path: $dir"
        ls -ldn "$dir"

        test -d "$dir"
        test -r "$dir"
        test -w "$dir"
        test -x "$dir"

        probe="$dir/.mailhub-write-test-$$"
        printf "mailhub-storage-self-test\n" > "$probe"
        test -s "$probe"
        grep -q "mailhub-storage-self-test" "$probe"
        rm -f "$probe"

        echo "READ_OK WRITE_OK TRAVERSE_OK"
      done
    '
}

echo
echo "[2/4] Backend..."
test_container_storage backend

echo
echo "[3/4] Worker..."
test_container_storage worker

echo
echo "[4/4] Verifierar att inga testfiler blev kvar..."
docker compose \
  --env-file .env \
  "${COMPOSE[@]}" \
  exec -T backend sh -ec '
    for dir in /data/attachments /data/routed; do
      if find "$dir" -maxdepth 1 -name ".mailhub-write-test-*" | grep -q .; then
        echo "Testfiler finns kvar i $dir" >&2
        exit 1
      fi
    done
  '

echo
echo "============================================================"
echo " Storage self test: OK"
echo "============================================================"
