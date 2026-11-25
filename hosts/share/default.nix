# Раздаваемая система (ISO для друзей). Что ставить — choices.json и packages.json рядом:
# их пишет установщик (этап 10) и программы «Настройка системы»/«Магазин».
# Здесь — значения по умолчанию для сборки образа и проверки в VM.
{ lib, ... }:
{
  imports = [ ./hardware-configuration.nix ];
  nextagg.share.choices = lib.importJSON ./choices.json;
  nextagg.share.packages = lib.importJSON ./packages.json;
  system.stateVersion = "26.05";
}
