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
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/mailhub}"
MAINTENANCE_STATUS_FILE="${CONTROL_DIR}/maintenance-status.json"
BACKUPS_FILE="${CONTROL_DIR}/backups.json"

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

cp "$REQUEST_FILE" "$CONTROL_DIR/.last-request.json"
chown 10001:10001 "$CONTROL_DIR/.last-request.json" 2>/dev/null || true
chmod 0660 "$CONTROL_DIR/.last-request.json" || true

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


maintenance_status() {
  local state="$1"
  local action="${2:-}"
  local backup_id="${3:-}"
  local message="${4:-}"
  local started="${5:-}"
  local finished="${6:-}"
  local tmp="${MAINTENANCE_STATUS_FILE}.tmp"

  jq -n \
    --arg state "$state" \
    --arg action "$action" \
    --arg backup_id "$backup_id" \
    --arg message "$message" \
    --arg started "$started" \
    --arg finished "$finished" \
    '{
      state: $state,
      action: (if ($action | length) > 0 then $action else null end),
      backup_id: (if ($backup_id | length) > 0 then $backup_id else null end),
      started_at: (if ($started | length) > 0 then $started else null end),
      finished_at: (if ($finished | length) > 0 then $finished else null end),
      message: (if ($message | length) > 0 then $message else null end)
    }' > "$tmp"

  jq -e . "$tmp" >/dev/null
  chown 10001:10001 "$tmp" 2>/dev/null || true
  chmod 0660 "$tmp"
  mv -f "$tmp" "$MAINTENANCE_STATUS_FILE"
}

refresh_backup_index() {
  mkdir -p "$BACKUP_ROOT"
  chmod 0700 "$BACKUP_ROOT"

  local tmp="${BACKUPS_FILE}.tmp"
  printf '[]\n' > "$tmp"

  local dir id created size database attachments routed has_env verified entry
  while IFS= read -r dir; do
    [[ -d "$dir" ]] || continue
    id="$(basename "$dir")"

    # Only expose safe basename identifiers through the web API.
    [[ "$id" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$ ]] || continue

    created="$(cat "$dir/created-at.txt" 2>/dev/null || true)"
    if [[ -z "$created" ]]; then
      created="$(date --iso-8601=seconds -r "$dir" 2>/dev/null || true)"
    fi

    size="$(du -sb "$dir" 2>/dev/null | awk '{print $1}')"
    database="$(stat -c '%s' "$dir/database.dump" 2>/dev/null || echo 0)"
    attachments="$(stat -c '%s' "$dir/attachments.tgz" 2>/dev/null || echo 0)"
    routed="$(stat -c '%s' "$dir/routed.tgz" 2>/dev/null || echo 0)"

    [[ -s "$dir/env.backup" ]] && has_env=true || has_env=false
    [[ -f "$dir/.verified" ]] && verified=true || verified=false

    entry="$(
      jq -n \
        --arg id "$id" \
        --arg created "$created" \
        --argjson size "${size:-0}" \
        --argjson database "${database:-0}" \
        --argjson attachments "${attachments:-0}" \
        --argjson routed "${routed:-0}" \
        --argjson has_env "$has_env" \
        --argjson verified "$verified" \
        '{
          id: $id,
          created_at: (if ($created | length) > 0 then $created else null end),
          size_bytes: $size,
          database_bytes: $database,
          attachments_bytes: $attachments,
          routed_bytes: $routed,
          has_environment: $has_env,
          sha256_verified: $verified
        }'
    )"

    jq --argjson item "$entry" '. + [$item]' "$tmp" > "${tmp}.next"
    mv -f "${tmp}.next" "$tmp"
  done < <(find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -print | sort -r)

  jq -e . "$tmp" >/dev/null
  chown 10001:10001 "$tmp" 2>/dev/null || true
  chmod 0660 "$tmp"
  mv -f "$tmp" "$BACKUPS_FILE"
}

safe_backup_path() {
  local id="$1"
  [[ "$id" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$ ]] || return 1

  local path="$BACKUP_ROOT/$id"
  [[ -d "$path" ]] || return 1

  local root_real path_real
  root_real="$(readlink -f "$BACKUP_ROOT")"
  path_real="$(readlink -f "$path")"

  [[ "$path_real" == "$root_real/"* ]] || return 1
  printf '%s\n' "$path_real"
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


backup_list)
  STARTED="$(date --iso-8601=seconds)"
  maintenance_status \
    "refreshing" "backup_list" "" \
    "Backuphistoriken uppdateras." \
    "$STARTED"

  if refresh_backup_index; then
    maintenance_status \
      "success" "backup_list" "" \
      "Backuphistoriken uppdaterades." \
      "$STARTED" "$(date --iso-8601=seconds)"
  else
    maintenance_status \
      "error" "backup_list" "" \
      "Backuphistoriken kunde inte uppdateras." \
      "$STARTED" "$(date --iso-8601=seconds)"
    exit 1
  fi
  ;;

backup_create)
  STARTED="$(date --iso-8601=seconds)"
  BACKUP_ID="mailhub-$(date -u +%Y%m%dT%H%M%SZ)"
  BACKUP_DIR="$BACKUP_ROOT/$BACKUP_ID"

  maintenance_status \
    "creating" "backup_create" "$BACKUP_ID" \
    "Backup skapas." \
    "$STARTED"

  mkdir -p "$BACKUP_ROOT"
  chmod 0700 "$BACKUP_ROOT"

  {
    echo
    echo "===== $(date --iso-8601=seconds) Web backup ====="
    chmod +x "$APP_DIR/scripts/backup.sh"
    "$APP_DIR/scripts/backup.sh" "$BACKUP_DIR"
    touch "$BACKUP_DIR/.verified"
  } >>"$LOG_FILE" 2>&1 || {
    maintenance_status \
      "error" "backup_create" "$BACKUP_ID" \
      "Backup misslyckades. Se update.log." \
      "$STARTED" "$(date --iso-8601=seconds)"
    refresh_backup_index || true
    exit 1
  }

  refresh_backup_index
  maintenance_status \
    "success" "backup_create" "$BACKUP_ID" \
    "Backup skapades." \
    "$STARTED" "$(date --iso-8601=seconds)"
  ;;

backup_restore)
  STARTED="$(date --iso-8601=seconds)"
  BACKUP_ID="$(jq -r '.backup_id // empty' "$CONTROL_DIR/.last-request.json" 2>/dev/null || true)"

  # For restore, the request payload is saved before REQUEST_FILE is removed.
  if [[ -z "$BACKUP_ID" ]]; then
    maintenance_status \
      "error" "backup_restore" "" \
      "Backup-ID saknas." \
      "$STARTED" "$(date --iso-8601=seconds)"
    exit 1
  fi

  TARGET_DIR="$(safe_backup_path "$BACKUP_ID" || true)"
  if [[ -z "$TARGET_DIR" ]]; then
    maintenance_status \
      "error" "backup_restore" "$BACKUP_ID" \
      "Vald backup finns inte eller har ogiltigt ID." \
      "$STARTED" "$(date --iso-8601=seconds)"
    exit 1
  fi

  maintenance_status \
    "restoring" "backup_restore" "$BACKUP_ID" \
    "Skapar säkerhetsbackup före återställning." \
    "$STARTED"

  SAFETY_ID="pre-restore-$(date -u +%Y%m%dT%H%M%SZ)"
  SAFETY_DIR="$BACKUP_ROOT/$SAFETY_ID"

  {
    echo
    echo "===== $(date --iso-8601=seconds) Pre-restore safety backup ====="
    chmod +x "$APP_DIR/scripts/backup.sh" "$APP_DIR/scripts/restore.sh"
    "$APP_DIR/scripts/backup.sh" "$SAFETY_DIR"
    touch "$SAFETY_DIR/.verified"

    maintenance_status \
      "restoring" "backup_restore" "$BACKUP_ID" \
      "Återställer vald backup. Webbgränssnittet kan startas om." \
      "$STARTED"

    echo
    echo "===== $(date --iso-8601=seconds) Web restore: $BACKUP_ID ====="
    "$APP_DIR/scripts/restore.sh" "$TARGET_DIR"
  } >>"$LOG_FILE" 2>&1 || {
    maintenance_status \
      "error" "backup_restore" "$BACKUP_ID" \
      "Återställningen misslyckades. Säkerhetsbackup: $SAFETY_ID." \
      "$STARTED" "$(date --iso-8601=seconds)"
    refresh_backup_index || true
    exit 1
  }

  refresh_backup_index
  maintenance_status \
    "success" "backup_restore" "$BACKUP_ID" \
    "Backup återställd. Säkerhetsbackup skapades som $SAFETY_ID." \
    "$STARTED" "$(date --iso-8601=seconds)"
  ;;

  *)
    json_status \
      "error" false \
      "" "" \
      "Okänd uppdateringsbegäran."
    exit 1
    ;;
esac

rm -f "$CONTROL_DIR/.last-request.json" 2>/dev/null || true
