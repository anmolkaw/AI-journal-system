#!/usr/bin/env bash
set -euo pipefail

base="${1:-http://127.0.0.1:3000/api/proxy}"
body_file="${TMPDIR:-/tmp}/ai-journal-smoke-body.json"
user="matrix_$(date +%s)"
password="TestPass_42"

request() {
  local label="$1"
  local expected="$2"
  local method="$3"
  local path="$4"
  local payload="${5-}"
  local auth="${6-}"
  local args=(-sS -o "$body_file" -w "%{http_code}" -X "$method")

  if [[ -n "$payload" ]]; then
    args+=(-H "Content-Type: application/json" --data "$payload")
  fi
  if [[ -n "$auth" ]]; then
    args+=(-H "Authorization: Bearer $auth")
  fi

  local status
  status="$(curl "${args[@]}" "$base$path")"
  if [[ "$status" != "$expected" ]]; then
    echo "FAIL $label expected=$expected actual=$status"
    jq -c . "$body_file" 2>/dev/null || true
    exit 1
  fi
  echo "PASS $label ($status)"
}

request "invalid registration" 422 POST "/auth/register" '{"username":"x","password":"short"}'
request "register" 201 POST "/auth/register" "{\"username\":\"$user\",\"password\":\"$password\"}"
token="$(jq -r .accessToken "$body_file")"
request "duplicate registration" 409 POST "/auth/register" "{\"username\":\"$user\",\"password\":\"$password\"}"
request "invalid login" 401 POST "/auth/login" "{\"username\":\"$user\",\"password\":\"WrongPass_42\"}"
request "valid login" 200 POST "/auth/login" "{\"username\":\"$user\",\"password\":\"$password\"}"
token="$(jq -r .accessToken "$body_file")"
request "missing authorization" 401 GET "/journal"
request "cross-user create denied" 403 POST "/journal" '{"userId":"another_user","ambience":"forest","text":"Private"}' "$token"
request "invalid ambience" 422 POST "/journal" '{"ambience":"space","text":"Invalid"}' "$token"
request "empty journal" 422 POST "/journal" '{"ambience":"forest","text":"   "}' "$token"
request "create journal" 201 POST "/journal" '{"ambience":"ocean","text":"The waves helped me feel steady and optimistic about tomorrow."}' "$token"
entry_id="$(jq -r .id "$body_file")"
request "list journals" 200 GET "/journal" "" "$token"
request "assignment list alias" 200 GET "/journal/$user" "" "$token"
request "cross-user list denied" 403 GET "/journal/another_user" "" "$token"
request "missing analysis source" 422 POST "/journal/analyze" '{}' "$token"
request "two analysis sources" 422 POST "/journal/analyze" "{\"entryId\":$entry_id,\"text\":\"duplicate source\"}" "$token"
request "missing journal analysis" 404 POST "/journal/analyze" '{"entryId":99999999}' "$token"
request "entry analysis" 200 POST "/journal/analyze" "{\"entryId\":$entry_id}" "$token"
analysis_first="$(jq -cS . "$body_file")"
request "cached entry analysis" 200 POST "/journal/analyze" "{\"entryId\":$entry_id}" "$token"
analysis_second="$(jq -cS . "$body_file")"
[[ "$analysis_first" == "$analysis_second" ]] || {
  echo "FAIL cached analysis changed"
  exit 1
}
echo "PASS cached analysis is stable"
request "raw text analysis" 200 POST "/journal/analyze" '{"text":"I feel quietly focused while planning the next careful step."}' "$token"
request "insights" 200 GET "/journal/insights" "" "$token"
jq -e '.totalEntries == 1 and (.topEmotion | type == "string") and .mostUsedAmbience == "ocean"' "$body_file" >/dev/null
echo "PASS insight aggregation values"
request "assignment insights alias" 200 GET "/journal/insights/$user" "" "$token"
request "cross-user insights denied" 403 GET "/journal/insights/another_user" "" "$token"

echo "Proxy/API matrix completed successfully"
