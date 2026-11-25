nixos_log_to_stdout() {
  [[ ${NIXOS_LOG_TO_STDOUT:-} == "1" || -z ${NIXOS_INSTALL_LOG_FILE:-} ]]
}

nixos_log_line() {
  if nixos_log_to_stdout; then
    echo "$1"
  else
    echo "$1" >>"$NIXOS_INSTALL_LOG_FILE"
  fi
}

start_install_log() {
  if ! nixos_log_to_stdout; then
    mkdir -p "$(dirname "$NIXOS_INSTALL_LOG_FILE")"
    touch "$NIXOS_INSTALL_LOG_FILE"
    chmod 666 "$NIXOS_INSTALL_LOG_FILE" 2>/dev/null || true
  fi

  export NIXOS_START_TIME="${NIXOS_START_TIME:-$(date '+%Y-%m-%d %H:%M:%S')}"
  export NIXOS_START_EPOCH="${NIXOS_START_EPOCH:-$(date +%s)}"

  nixos_log_line "=== NixOS Setup Started: $NIXOS_START_TIME ==="
}

stop_install_log() {
  local end_time end_epoch duration mins secs
  end_time=$(date '+%Y-%m-%d %H:%M:%S')
  end_epoch=$(date +%s)

  nixos_log_line "=== NixOS Setup Completed: $end_time ==="

  if [[ -n ${NIXOS_START_EPOCH:-} ]]; then
    duration=$((end_epoch - NIXOS_START_EPOCH))
    mins=$((duration / 60))
    secs=$((duration % 60))
    nixos_log_line "NixOS setup: ${mins}m ${secs}s"
  fi
}

run_logged() {
  local script="$1"
  local exit_code errexit_was_set=0

  nixos_log_line "[$(date '+%Y-%m-%d %H:%M:%S')] Starting: $script"

  case $- in
    *e*)
      errexit_was_set=1
      set +e
      ;;
  esac

  local runner=(bash -eE)
  if [[ ${NIXOS_INSTALL_DEBUG:-} == "1" ]]; then
    runner=(bash -x -eE)
  fi

  if nixos_log_to_stdout; then
    PS4='+ ${BASH_SOURCE[0]##*/}:${LINENO}:${FUNCNAME[0]:-main}: ' \
      "${runner[@]}" -c 'source "$1"' bash "$script" </dev/null 2>&1
  else
    PS4='+ ${BASH_SOURCE[0]##*/}:${LINENO}:${FUNCNAME[0]:-main}: ' \
      "${runner[@]}" -c 'source "$1"' bash "$script" </dev/null >>"$NIXOS_INSTALL_LOG_FILE" 2>&1
  fi

  exit_code=$?
  (( errexit_was_set )) && set -e

  if (( exit_code == 0 )); then
    nixos_log_line "[$(date '+%Y-%m-%d %H:%M:%S')] Completed: $script"
  else
    nixos_log_line "[$(date '+%Y-%m-%d %H:%M:%S')] Failed: $script (exit code: $exit_code)"
  fi

  return $exit_code
}
