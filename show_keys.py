# https://github.com/qtile/qtile/issues/1329#issuecomment-1281322991

def show_keys(keys):
    """
    print current keybindings in a pretty way for a rofi/dmenu window.
    """
    key_help = ""
    text_replaced = {
        "mod4": "[MOD]",
        "control": "[CTRL]",
        "mod1": "[ALT]",
        "shift": "[SHIFT]",
        "Escape": "ESC",
    }
    for k in keys:
        mods = ""
        key = ""
        desc = k.desc.title()
        for m in k.modifiers:
            if m in text_replaced.keys():
                mods += text_replaced[m] + " + "
            else:
                mods += m.capitalize() + " + "

        if len(k.key) > 1:
            if k.key in text_replaced.keys():
                key = text_replaced[k.key]
            else:
                key = k.key.title()
        else:
            key = k.key

        key_line = "{:<30} {:<50} {}\n".format(mods + key, desc, k.commands[0].name)
        key_help += key_line

    return key_help
