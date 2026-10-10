#!/bin/sh
set -eu

usage() {
  printf 'Usage: %s [--profile personal|work]\n' "$0"
  printf 'Install agents, optionally pinning models from a deployment profile.\n'
  printf 'Target: OPENCODE_AGENT_DIR or ${XDG_CONFIG_HOME:-$HOME/.config}/opencode/agents\n'
}

profile=
while [ "$#" -gt 0 ]; do
  case "$1" in
    --profile)
      if [ "$#" -lt 2 ] || [ -n "$profile" ]; then
        printf 'Error: --profile requires one value and may be given only once.\n' >&2
        exit 2
      fi
      case "$2" in
        personal|work) profile=$2 ;;
        *) printf 'Error: unknown profile: %s (expected personal or work)\n' "$2" >&2; exit 2 ;;
      esac
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Error: unexpected argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
source_dir=$script_dir/agents
config_home=${XDG_CONFIG_HOME:-"$HOME/.config"}
target_dir=${OPENCODE_AGENT_DIR:-"$config_home/opencode/agents"}

if [ -n "$profile" ]; then
  if ! command -v python3 >/dev/null 2>&1; then
    printf 'Error: --profile requires Python 3.\n' >&2
    exit 1
  fi
  staging_dir=$(mktemp -d)
  trap 'rm -rf -- "$staging_dir"' EXIT
  trap 'exit 1' HUP INT TERM
  python3 "$script_dir/install-agent-profile.py" \
    "$script_dir/models-$profile.jsonc" "$source_dir" "$staging_dir"
  source_dir=$staging_dir
fi

install -d -m 0755 "$target_dir"

for source in "$source_dir"/*.md; do
  [ -f "$source" ] || continue
  install -m 0644 "$source" "$target_dir/$(basename "$source")"
done

printf 'Installed OpenCode agents in %s\n' "$target_dir"
if [ -n "$profile" ]; then
  printf 'Pinned installed agent models using the %s profile.\n' "$profile"
fi
printf 'Restart OpenCode to load the installed agents.\n'
