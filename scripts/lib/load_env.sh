#!/usr/bin/env bash
#
# Deployment environment-file loader for the host-level ops scripts.
#
# Source this file, then call `keeper_load_env` before reading settings:
#
#   . "${SCRIPT_DIR}/lib/load_env.sh"
#   keeper_load_env
#
# One resolution order for every script, matching
# `keeper_api.services.ops_env` and Compose (`env_file: ${KEEPER_ENV_FILE:-.env}`):
#
#   1. $KEEPER_ENV_FILE
#   2. <repo root>/.env
#
# Variables already present in the environment always win, so a single value can
# be overridden for one run. A missing file is not an error; the caller decides
# whether its own required settings are missing.
#
# Parsing rules (kept identical to the Python loader; asserted by
# tests/test_ops_env_loading.py): blank lines and `#` comment lines are skipped,
# a value may be wrapped in one layer of matching quotes, and inline `#`
# comments are not stripped. Keep comments on their own lines.

keeper_load_env() {
  local repo_root file line key value first last

  repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
  file="${KEEPER_ENV_FILE:-${repo_root}/.env}"
  [[ "${file}" = /* ]] || file="${repo_root}/${file}"
  [[ -f "${file}" ]] || return 0

  while IFS= read -r line || [[ -n "${line}" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "${line}" || "${line}" == \#* || "${line}" != *=* ]] && continue

    key="${line%%=*}"
    value="${line#*=}"
    key="${key#"${key%%[![:space:]]*}"}"
    key="${key%"${key##*[![:space:]]}"}"
    key="${key#export }"
    [[ "${key}" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue

    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    if [[ ${#value} -ge 2 ]]; then
      first="${value:0:1}"
      last="${value: -1}"
      if [[ ( "${first}" == '"' && "${last}" == '"' ) || ( "${first}" == "'" && "${last}" == "'" ) ]]; then
        value="${value:1:${#value}-2}"
      fi
    fi

    # Never clobber a value that is already set in the environment.
    [[ -n "${!key-}" ]] && continue
    export "${key}=${value}"
  done < "${file}"

  return 0
}
