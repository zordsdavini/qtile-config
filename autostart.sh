#!/bin/bash

[[ -f ~/.Xresources ]] && xrdb -merge ~/.Xresources
#[[ -f ~/.Xmodmap ]] && xmodmap ~/.Xmodmap
setxkbmap -layout us,lt -variant ,sgs -option grp:alt_space_toggle,compose:rctrl,lv3:ralt_switch
# setxkbmap -layout us,lt,ru -variant ,sgs,phonetic -option grp:alt_space_toggle,compose:rctrl,lv3:ralt_switch,caps:hyper
# blueman-applet &
# dunst &
CM_MAX_CLIPS=50 CM_SELECTIONS="clipboard primary" clipmenud &
flameshot &
picom -b
browserpass &
dbus-update-activation-environment --systemd DBUS_SESSION_BUS_ADDRESS DISPLAY XAUTHORITY
nextcloud &
udiskie -t &
hp-toolbox &
