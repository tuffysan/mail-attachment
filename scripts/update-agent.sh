#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/mail-attachment-hub}"
CONTROL_DIR="${CONTROL_DIR:-/var/lib/mailhub-control}"
REQUEST_FILE="${CONTROL_DIR}/request.json"
STATUS_FILE="${CONTROL_DIR}/status.json"
LOG_FILE="${CONTROL_DIR}/update.log"
LOCK_FILE="${CONTROL_DIR}/update.lock"
BRANCH="${BRANCH:-main}"
REMOTE="${REMOTE:-origin}"

write_emergency_status() {
  local code="$1"
  local message="$2"
  local tmp="${STATUS_FILE}.emergency.tmp"

  jq -n \
    --arg message "$message" \
    --arg checked_at "$(date --iso-8601=seconds)" \
    --argjson code "$code" \
    '{
      state: "error",
      installed_commit: null,
      latest_commit: null,
      update_available: false,
      latest_message: null,
      latest_date: null,
      checked_at: $checked_at,
      started_at: null,
      finished_at: $checked_at,
      message: ($message + " (exit " + ($code | tostring) + ")")
    }' > "$tmp" 2>/dev/null || return 0

  if [[ -s "$tmp" ]] && jq -e . "$tmp" >/dev/null 2>&1; then
    chown 10001:10001 "$tmp" 2>/dev/null || true
    chmod 0660 "$tmp" 2>/dev/null || true
    mv -f "$tmp" "$STATUS_FILE" 2>/dev/null || true
  else
    rm -f "$tmp"
  fi
}

agent_failure() {
  local code=$?
  write_emergency_status "$code" "Update-agenten avbröts oväntat."
  exit "$code"
}
trap agent_failure ERR

mkdir -p "$CONTROL_DIR"
touch "$LOG_FILE"
chown 10001:10001 "$LOG_FILE" 2>/dev/null || true
chmod 0660 "$LOG_FILE" || true

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  exit 0
fi

[[ -f "$REQUEST_FILE" ]] || exit 0

if ! jq -e . "$REQUEST_FILE" >/dev/null 2>&1; then
  rm -f "$REQUEST_FILE"
  write_emergency_status 2 "Uppdateringsbegäran innehöll ogiltig JSON."
  exit 2
fi

ACTION="$(jq -r '.action // empty' "$REQUEST_FILE")"
rm -f "$REQUEST_FILE"

json_status() {
  local state="$1"
  local available="$2"
  local current="${3:-}"
  local latest="${4:-}"
  local message="${5:-}"
  local latest_message="${6:-}"
  local latest_date="${7:-}"
  local started="${8:-}"
  local finished="${9:-}"

  local tmp="${STATUS_FILE}.tmp"

  jq -n \
    --arg state "$state" \
    --arg current "$current" \
    --arg latest "$latest" \
    --arg message "$message" \
    --arg latest_message "$latest_message" \
    --arg latest_date "$latest_date" \
    --arg started "$started" \
    --arg finished "$finished" \
    --arg checked_at "$(date --iso-8601=seconds)" \
    --argjson available "$available" \
    '{
      state: $state,
      installed_commit:
        (if ($current | length) > 0 then $current else null end),
      latest_commit:
        (if ($latest | length) > 0 then $latest else null end),
      update_available: $available,
      latest_message:
        (if ($latest_message | length) > 0 then $latest_message else null end),
      latest_date:
        (if ($latest_date | length) > 0 then $latest_date else null end),
      checked_at: $checked_at,
      started_at:
        (if ($started | length) > 0 then $started else null end),
      finished_at:
        (if ($finished | length) > 0 then $finished else null end),
      message:
        (if ($message | length) > 0 then $message else null end)
    }' > "$tmp"

  if [[ ! -s "$tmp" ]]; then
    echo "Generated update status JSON is empty." >&2
    rm -f "$tmp"
    return 1
  fi

  if ! jq -e . "$tmp" >/dev/null 2>&1; then
    echo "Generated update status JSON is invalid." >&2
    cat "$tmp" >&2 || true
    rm -f "$tmp"
    return 1
  fi

  chown 10001:10001 "$tmp" 2>/dev/null || true
  chmod 0660 "$tmp"
  mv -f "$tmp" "$STATUS_FILE"
}

get_versions() {
  cd "$APP_DIR"

  git fetch "$REMOTE" "$BRANCH" >>"$LOG_FILE" 2>&1

  CURRENT_COMMIT="$(git rev-parse HEAD)"
  LATEST_COMMIT="$(git rev-parse "${REMOTE}/${BRANCH}")"
  LATEST_MESSAGE="$(git log -1 --format=%s "${REMOTE}/${BRANCH}")"
  LATEST_DATE="$(git log -1 --format=%cI "${REMOTE}/${BRANCH}")"

  if [[ "$CURRENT_COMMIT" == "$LATEST_COMMIT" ]]; then
    UPDATE_AVAILABLE=false
  else
    UPDATE_AVAILABLE=true
  fi
}

case "$ACTION" in
  check)
    json_status \
      "checking" false \
      "" "" \
      "Kontrollerar GitHub."

    if get_versions; then
      if [[ "$UPDATE_AVAILABLE" == "true" ]]; then
        json_status \
          "update_available" true \
          "$CURRENT_COMMIT" \
          "$LATEST_COMMIT" \
          "En ny version finns på GitHub." \
          "$LATEST_MESSAGE" \
          "$LATEST_DATE"
      else
        json_status \
          "up_to_date" false \
          "$CURRENT_COMMIT" \
          "$LATEST_COMMIT" \
          "Installationen är uppdaterad." \
          "$LATEST_MESSAGE" \
          "$LATEST_DATE"
      fi
    else
      json_status \
        "error" false \
        "" "" \
        "Kunde inte kontrollera GitHub."
      exit 1
    fi
    ;;

  update)
    STARTED="$(date --iso-8601=seconds)"

    if ! get_versions; then
      json_status \
        "error" false \
        "" "" \
        "Kunde inte läsa GitHub före uppdatering." \
        "" "" \
        "$STARTED"
      exit 1
    fi

    if [[ "$UPDATE_AVAILABLE" != "true" ]]; then
      json_status \
        "up_to_date" false \
        "$CURRENT_COMMIT" \
        "$LATEST_COMMIT" \
        "Installationen är redan uppdaterad." \
        "$LATEST_MESSAGE" \
        "$LATEST_DATE" \
        "$STARTED" \
        "$(date --iso-8601=seconds)"
      exit 0
    fi

    json_status \
      "updating" true \
      "$CURRENT_COMMIT" \
      "$LATEST_COMMIT" \
      "Uppdatering pågår. Webbgränssnittet kan startas om." \
      "$LATEST_MESSAGE" \
      "$LATEST_DATE" \
      "$STARTED"

    {
      echo
      echo "===== $(date --iso-8601=seconds) Web update ====="
      chmod +x "$APP_DIR/scripts/lxc-update.sh"
      "$APP_DIR/scripts/lxc-update.sh"
    } >>"$LOG_FILE" 2>&1 || {
      json_status \
        "error" true \
        "$CURRENT_COMMIT" \
        "$LATEST_COMMIT" \
        "Uppdateringen misslyckades. Se /var/lib/mailhub-control/update.log." \
        "$LATEST_MESSAGE" \
        "$LATEST_DATE" \
        "$STARTED" \
        "$(date --iso-8601=seconds)"
      exit 1
    }

    cd "$APP_DIR"
    NEW_COMMIT="$(git rev-parse HEAD)"

    git fetch "$REMOTE" "$BRANCH" >>"$LOG_FILE" 2>&1 || true

    NEW_LATEST="$(git rev-parse "${REMOTE}/${BRANCH}" 2>/dev/null || echo "$NEW_COMMIT")"
    NEW_MESSAGE="$(git log -1 --format=%s "${REMOTE}/${BRANCH}" 2>/dev/null || true)"
    NEW_DATE="$(git log -1 --format=%cI "${REMOTE}/${BRANCH}" 2>/dev/null || true)"

    json_status \
      "success" false \
      "$NEW_COMMIT" \
      "$NEW_LATEST" \
      "Uppdateringen slutfördes." \
      "$NEW_MESSAGE" \
      "$NEW_DATE" \
      "$STARTED" \
      "$(date --iso-8601=seconds)"
    ;;

  *)
    json_status \
      "error" false \
      "" "" \
      "Okänd uppdateringsbegäran."
    exit 1
    ;;
esac
