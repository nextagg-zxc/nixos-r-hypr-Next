echo "Rename the model usage widget to agents and prime its data files"

# The widget formerly known as nixos.model-usage is now nixos.agents, and
# it no longer scans providers itself: it displays the records that
# nixos-agent-usage-update writes under ~/.local/state/nixos/agents/usage/.
# Rename the widget wherever a user's config mentions it — bar layout entries
# keep their settings, a disabled widget stays disabled — then generate the
# records once so the bar doesn't sit empty until the widget's first refresh
# timer, and drop the old scanner's cache directory, which nothing reads
# anymore.

config_file="$HOME/.config/nixos/shell.json"

if [[ -s $config_file ]]; then
  tmp=$(mktemp)
  jq '
    def rename:
      if . == "nixos.model-usage" then
        "nixos.agents"
      elif type == "object" and .id == "nixos.model-usage" then
        .id = "nixos.agents"
      else
        .
      end;

    (if (.bar.layout? | type) == "object" then
      .bar.layout |= map_values(if type == "array" then map(rename) else . end)
    else . end)
    | (if (.disabledPlugins? | type) == "array" then
      .disabledPlugins |= map(rename)
    else . end)
  ' "$config_file" >"$tmp" && mv "$tmp" "$config_file" || rm -f "$tmp"
fi

rm -rf "$HOME/.cache/nixos/model-usage"

nixos-agent-usage-update || true
