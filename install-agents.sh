#!/bin/sh
set -eu

source_dir=$(CDPATH= cd -- "$(dirname -- "$0")/agents" && pwd)
config_home=${XDG_CONFIG_HOME:-"$HOME/.config"}
target_dir=${OPENCODE_AGENT_DIR:-"$config_home/opencode/agents"}

install -d -m 0755 "$target_dir"

for source in "$source_dir"/*.md; do
  [ -f "$source" ] || continue
  install -m 0644 "$source" "$target_dir/$(basename "$source")"
done

printf 'Installed OpenCode agents in %s\n' "$target_dir"
