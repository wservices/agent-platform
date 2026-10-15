#!/usr/bin/env bash
# Idempotently provision the agents/ group hierarchy and repositories on GitLab.
#
# Requires a GitLab Personal/Project Access Token with `api` scope in
# $GITLAB_TOKEN. Host defaults to gitlab.wservices.ch. Never prints the token.
#
# Usage:
#   GITLAB_TOKEN=xxxxx ./gitlab_provision.sh ensure-group  agents
#   GITLAB_TOKEN=xxxxx ./gitlab_provision.sh ensure-subgroup agents cybersecurity
#   GITLAB_TOKEN=xxxxx ./gitlab_provision.sh ensure-project  agents/cybersecurity security-analyst
#
# It checks existence before creating, so re-running is safe.
set -euo pipefail

HOST="${GITLAB_HOST:-gitlab.wservices.ch}"
API="https://${HOST}/api/v4"

die() { echo "error: $*" >&2; exit 1; }
[ -n "${GITLAB_TOKEN:-}" ] || die "GITLAB_TOKEN not set (needs 'api' scope)"

# urlencode a path like agents/cybersecurity -> agents%2Fcybersecurity
enc() { python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1],safe=""))' "$1"; }

api() { # method path [data]
  local method="$1" path="$2" data="${3:-}"
  if [ -n "$data" ]; then
    curl -sS --fail-with-body -X "$method" \
      --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
      --data "$data" "${API}${path}"
  else
    curl -sS --fail-with-body -X "$method" \
      --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" "${API}${path}"
  fi
}

group_id() { # full_path -> prints numeric id or empty
  api GET "/groups/$(enc "$1")" 2>/dev/null | python3 -c \
    'import sys,json;
try: print(json.load(sys.stdin)["id"])
except Exception: pass'
}

project_exists() { # full_path -> 0 if exists
  api GET "/projects/$(enc "$1")" >/dev/null 2>&1
}

cmd="${1:-}"; shift || true
case "$cmd" in
  ensure-group)
    full="$1"
    if [ -n "$(group_id "$full")" ]; then echo "group $full exists"; else
      api POST "/groups" "name=${full}&path=${full}" >/dev/null && echo "created group $full"
    fi ;;
  ensure-subgroup)
    parent="$1"; name="$2"; full="${parent}/${name}"
    if [ -n "$(group_id "$full")" ]; then echo "subgroup $full exists"; else
      pid="$(group_id "$parent")"; [ -n "$pid" ] || die "parent group $parent not found"
      api POST "/groups" "name=${name}&path=${name}&parent_id=${pid}" >/dev/null \
        && echo "created subgroup $full"
    fi ;;
  ensure-project)
    ns="$1"; name="$2"; full="${ns}/${name}"
    if project_exists "$full"; then echo "project $full exists"; else
      nsid="$(group_id "$ns")"; [ -n "$nsid" ] || die "namespace $ns not found"
      api POST "/projects" "name=${name}&path=${name}&namespace_id=${nsid}&visibility=private&default_branch=main" >/dev/null \
        && echo "created project $full"
    fi ;;
  *)
    die "usage: $0 {ensure-group|ensure-subgroup|ensure-project} ..." ;;
esac
