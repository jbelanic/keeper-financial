#!/bin/bash
set -euo pipefail
TOKEN='eyJhbGciOiJFUzI1NiIsImtpZCI6IjQwYjAwZTZhLWFjNTgtNDc0OS1hYmQ2LTdhZmUwMjJkMjVjOSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwOi8vMTI3LjAuMC4xOjU0MzIxL2F1dGgvdjEiLCJzdWIiOiJlNTA3ZjdlNC05ZTc2LTQ1OTEtOTg5MC1mNzlkZDQ1ZGE0MDMiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiaXhwIjoxNzkxMzgxMzc3LCJpYXQiOjE3OTEzNzc3NzcsImVtYWlsIjoiYWRtaW5AZXhhbXBsZS50ZXN0IiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3OTEzNzc3Nzd9XSwic2Vzc2lvbl9pZCI6ImQwMzNlNTE1LWE2ZmQtNGMwMS1iMWM3LWVhMmMxYjIzYTQ3YSIsImlzX2Fub255bW91cyI6ZmFsc2V9.cR9THD9XoVLFxrWsMxtq-MiCqGFwd38fN_FPUIwPD1SSj0dDpp7yIE3NEiTeX28FnAp3Tx-LEgm4MZ_wQzaBqg'
FACTOR='328dc1dd-6756-4f0b-8cce-44845a2c7514'

echo '--- GET /auth/v1/user ---'
curl -sS -i -H "Authorization: Bearer $TOKEN" http://127.0.0.1:54321/auth/v1/user || true

echo '\n--- GET /auth/v1/factors/<id> ---'
curl -sS -i -H "Authorization: Bearer $TOKEN" http://127.0.0.1:54321/auth/v1/factors/$FACTOR || true

echo '\n--- GET /auth/v1/factors (list) ---'
curl -sS -i -H "Authorization: Bearer $TOKEN" http://127.0.0.1:54321/auth/v1/factors || true
