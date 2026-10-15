#!/usr/bin/env bash
# Publish a private source repo to the PUBLIC open-core mirror on gitlab.com.
#
# Private gitlab.wservices.ch stays the source of truth; this pushes a scrubbed
# open-core copy to gitlab.com/<group>/<public-name> (flat naming, since
# gitlab.com has no nested subgroups under a user/one-group mirror here).
#
# Naming convention: profiles -> agent-<role>, skills -> skill-<name>,
# framework -> platform.
#
# Requires: glab authenticated to gitlab.com (PAT scope `api`) for --create, and
# push access (glab HTTPS credential or an SSH key registered on gitlab.com).
# Never prints tokens.
#
# Usage:
#   publish_mirror.sh <src_dir> <public_name> [--create] [--tags] [--ssh]
# Env:
#   MIRROR_HOST   default gitlab.com
#   MIRROR_GROUP  default wservices
#
# Steps: secret-scan gate -> (optional) create public project -> set 'public'
# remote -> push main (+ tags). Refuses to push if the secret scan finds anything.
set -euo pipefail

HOST="${MIRROR_HOST:-gitlab.com}"
GROUP="${MIRROR_GROUP:-wservices}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SRC="${1:-}"; NAME="${2:-}"; shift 2 2>/dev/null || true
CREATE=0; TAGS=0; USE_SSH=0
for a in "$@"; do case "$a" in
  --create) CREATE=1;; --tags) TAGS=1;; --ssh) USE_SSH=1;;
  *) echo "unknown arg: $a" >&2; exit 2;; esac; done

[ -n "$SRC" ] && [ -n "$NAME" ] && [ -d "$SRC/.git" ] || {
  echo "usage: publish_mirror.sh <src_dir> <public_name> [--create] [--tags] [--ssh]" >&2; exit 2; }

echo "== secret-scan gate on $SRC =="
python3 "$HERE/../ci/secret_scan.py" "$SRC" || { echo "ABORT: secret scan found something" >&2; exit 1; }

if [ "$CREATE" -eq 1 ]; then
  echo "== ensure public project $GROUP/$NAME on $HOST =="
  export GITLAB_HOST="$HOST"
  if glab api "projects/$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=''))" "$GROUP/$NAME")" >/dev/null 2>&1; then
    echo "   exists"
  else
    nsid=$(glab api "groups/$GROUP" 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin).get("id",""))')
    [ -n "$nsid" ] || { echo "ABORT: group $GROUP not found on $HOST (create it / check auth)" >&2; exit 1; }
    glab api -X POST projects -f "name=$NAME" -F "namespace_id=$nsid" -f visibility=public -f default_branch=main >/dev/null
    echo "   created (public)"
  fi
fi

if [ "$USE_SSH" -eq 1 ]; then REMOTE="git@$HOST:$GROUP/$NAME.git"; else REMOTE="https://$HOST/$GROUP/$NAME.git"; fi
echo "== set 'public' remote -> $REMOTE =="
git -C "$SRC" remote remove public 2>/dev/null || true
git -C "$SRC" remote add public "$REMOTE"

echo "== push main =="
git -C "$SRC" push public main
if [ "$TAGS" -eq 1 ]; then echo "== push tags =="; git -C "$SRC" push public --tags; fi

echo "== verify remote main =="
local_head="$(git -C "$SRC" rev-parse HEAD)"
remote_head="$(git -C "$SRC" ls-remote public refs/heads/main | awk '{print $1}')"
[ "$local_head" = "$remote_head" ] && echo "OK  $GROUP/$NAME -> $remote_head" \
  || { echo "MISMATCH local=$local_head remote=$remote_head" >&2; exit 1; }
