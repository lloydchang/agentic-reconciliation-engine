#!/usr/bin/env bash
# Helper utilities for detecting POSIX shells under Windows/WSL environments.
set -euo pipefail
cd $(dirname $0)

_log_message() {
  local logger=$1 fallback=$2 message=$3
  local fn_type
  fn_type=$(type -t "$logger" 2>/dev/null || true)
  if [[ -n "$logger" && "$fn_type" == "function" ]]; then
    "$logger" "$message"
  else
    printf "%s %s\n" "$fallback" "$message"
  fi
}

is_windows_shell() {
  local os_name="${OS:-}"
  local uname_s
  uname_s=$(uname -s 2>/dev/null || true)
  if [[ "$os_name" == "Windows_NT" ]]; then
    return 0
  fi
  case "$uname_s" in
    MINGW*|MSYS*|CYGWIN*)
      return 0
      ;;
  esac
  return 1
}

is_wsl() {
  if [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
    return 0
  fi
  if [[ -f /proc/version ]] && grep -qi microsoft /proc/version; then
    return 0
  fi
  if [[ -f /proc/sys/kernel/osrelease ]] && grep -qi microsoft /proc/sys/kernel/osrelease; then
    return 0
  fi
  local release
  release=$(uname -r 2>/dev/null || true)
  if [[ "$release" == *Microsoft* ]] || [[ "$release" == *microsoft* ]]; then
    return 0
  fi
  return 1
}

ensure_wsl_sanity() {
  local script_name=${1:-"script"}
  local warn_logger=${2:-warn}
  local info_logger=${3:-info}
  if is_windows_shell && ! is_wsl; then
    local uname_s
    uname_s=$(uname -s 2>/dev/null || true)
    _log_message "$warn_logger" "WARN" "[WSL check] ${script_name} is running in ${uname_s:-Windows} without WSL/Git Bash. Use a POSIX-compatible shell (WSL, Git Bash, msys2) to avoid tool failures."
  elif is_wsl; then
    _log_message "$info_logger" "INFO" "[WSL check] ${script_name} verified WSL environment."
  fi
}

WINDOWS_SHELL_ENVIRONMENT=false
WSL_ENVIRONMENT=false
if is_windows_shell; then
  WINDOWS_SHELL_ENVIRONMENT=true
fi
if is_wsl; then
  WSL_ENVIRONMENT=true
fi

export WINDOWS_SHELL_ENVIRONMENT WSL_ENVIRONMENT
