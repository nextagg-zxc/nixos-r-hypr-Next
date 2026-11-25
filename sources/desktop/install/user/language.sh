# A language the install media preset (/etc/nixos/language) becomes this
# user's desktop language; the system step generated its locale.
code=
[[ -r /etc/nixos/language ]] && read -r code </etc/nixos/language
if [[ -n $code ]]; then
  "$NIXOS_PATH/bin/nixos-language" seed "$code" || echo "Could not set the preset language $code" >&2
fi
