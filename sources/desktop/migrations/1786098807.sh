echo "Relink agent skill symlinks to default/agents/skills/nixos"

mkdir -p ~/.agents/skills ~/.claude/skills ~/.codex/skills ~/.pi/agent/skills
ln -sfn "$NIXOS_PATH/default/agents/skills/nixos" ~/.agents/skills/nixos
ln -sfn "$NIXOS_PATH/default/agents/skills/nixos" ~/.claude/skills/nixos
ln -sfn "$NIXOS_PATH/default/agents/skills/nixos" ~/.codex/skills/nixos
ln -sfn "$NIXOS_PATH/default/agents/skills/nixos" ~/.pi/agent/skills/nixos
