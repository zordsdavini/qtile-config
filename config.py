# Copyright (c) 2019 Zordsdavini
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from libqtile.config import EzKey as Key, Screen, Group, Drag, Click
from libqtile.command import lazy
from libqtile import layout, bar, widget, extension, hook
from subprocess import call, check_output
import xrp
import json
from os import path, getenv

from typing import List  # noqa: F401

"""
TODO
====

2. integrate XF86Tools

improve Qtile:
-------------

2. tooltips
3. mouse clicks to all widgets
6. theme extension
7. restore POMODORE on qtile restart

"""

# monadtall extention to follow maximized window if we have only two
@lazy.function
def z_maximize(qtile):
    layout = qtile.current_layout
    group = qtile.current_group
    layout.cmd_maximize()
    if len(group.windows) == 2:
        fw = qtile.current_window
        ow = None
        # get other window
        for w in group.windows:
            if w != fw:
                ow = w

        if ow and fw.info()['width'] < ow.info()['width']:
            layout.cmd_next()


# keyboard next layout
@lazy.function
def z_next_keyboard(qtile):
    keyboard_widget.cmd_next_keyboard()


class Commands:
    autorandr = ['autorandr', '-c']
    fehbg = ['sh', '~/.fehbg']
    alsamixer = 'st -e alsamixer'
    update = "st -e yay -Syu"
    volume_up = 'amixer -q -c 0 sset Master 5dB+'
    volume_down = 'amixer -q -c 0 sset Master 5dB-'
    volume_toggle = 'amixer -q set Master toggle'
    mic_toggle = 'amixer -q set Dmic0 toggle'
    screenshot_all = 'zscrot'
    screenshot_window = 'zscrot u'
    screenshot_selection = 'zscrot s'
    brightness_up = 'light -A 5'
    brightness_down = 'light -U 5'

    def reload_screen(self):
        call(self.autorandr)
        call(self.fehbg)

    def get_watson_status(self):
        w_stat = check_output(['watson', 'status'])
        return w_stat.decode("utf-8").replace('\n', '')


commands = Commands()

xresources = path.realpath(getenv('HOME') + '/.Xresources')
result = xrp.parse_file(xresources, 'utf-8')
font_data = result.resources['*.font'].split(':')
FONT = font_data[0]
FONT_SIZE = int(font_data[1].split('=')[1])

color_data = json.loads(open(getenv('HOME')+'/.cache/wal/colors.json').read())
# BLACK = color_data['colors']['color0']
# BLACK = "#15181a"
BLACK = "#1A1C1D"
RED = color_data['colors']['color1']
GREEN = color_data['colors']['color2']
YELLOW = color_data['colors']['color3']
BLUE = color_data['colors']['color4']
MAGENTA = color_data['colors']['color5']
CYAN = color_data['colors']['color6']
WHITE = color_data['colors']['color7']

keys = [
    # Switch between windows
    Key("M-h", lazy.layout.left()),
    Key("M-l", lazy.layout.right()),
    Key("M-j", lazy.layout.down()),
    Key("M-k", lazy.layout.up()),

    # Move windows
    Key("M-S-h", lazy.layout.shuffle_left()),
    Key("M-S-l", lazy.layout.shuffle_right()),
    Key("M-S-j", lazy.layout.shuffle_down()),
    Key("M-S-k", lazy.layout.shuffle_up()),

    # Grow windows
    Key("M-C-h", lazy.layout.grow_left()),
    Key("M-C-l", lazy.layout.grow_right()),
    Key("M-C-j", lazy.layout.grow_down()),
    Key("M-C-k", lazy.layout.grow_up()),

    # Flip windows
    Key("M-A-h", lazy.layout.flip_left()),
    Key("M-A-l", lazy.layout.flip_right()),
    Key("M-A-j", lazy.layout.flip_down()),
    Key("M-A-k", lazy.layout.flip_up()),

    Key("M-S-<Return>", lazy.layout.toggle_split()),

    # Monadtall additional
    Key("M-i", lazy.layout.grow()),
    Key("M-m", lazy.layout.shrink()),
    Key("M-o", z_maximize, desc='maximize window'),
    Key("M-n", lazy.layout.reset(), desc='reset layout'),
    Key("M-S-<space>", lazy.layout.flip()),

    # Switch window focus to other pane(s) of stack
    Key("M-<space>", lazy.layout.next(), desc='next window'),

    # Focus screen
    Key("M-<comma>", lazy.prev_screen()),
    Key("M-<period>", lazy.next_screen()),

    Key("M-<Return>", lazy.spawn("st -e tmux")),
    Key("A-S-<space>", z_next_keyboard, desc='switch keyboard layout'),
    Key("M-<Tab>", lazy.next_layout()),
    Key("M-S-w", lazy.window.kill(), desc='close window'),

    Key("M-S-x", lazy.hide_show_bar("top"), desc='toggle top bar'),
    Key("M-C-x", lazy.hide_show_bar("bottom"), desc='toggle bottom bar'),

    Key("M-C-r", lazy.restart()),
    Key("M-C-f", lazy.window.toggle_floating()),

    # Sound
    Key('<XF86AudioRaiseVolume>', lazy.spawn(Commands.volume_up)),
    Key('<XF86AudioLowerVolume>', lazy.spawn(Commands.volume_down)),
    Key('M-<Up>', lazy.spawn(Commands.volume_up)),
    Key('M-<Down>', lazy.spawn(Commands.volume_down)),
    Key('<XF86AudioMute>', lazy.spawn(Commands.volume_toggle)),
    Key('<XF86AudioMicMute>', lazy.spawn(Commands.mic_toggle)),

    # Other FN keys
    Key('<XF86MonBrightnessUp>', lazy.spawn(Commands.brightness_up)),
    Key('<XF86MonBrightnessDown>', lazy.spawn(Commands.brightness_down)),
    Key('<XF86Display>', lazy.spawn('arandr')),
    Key('<XF86Favorites>', lazy.spawn('touchpad_toggle'), desc='on/off touchpad'),

    # Screenshot
    Key('<Print>', lazy.spawn(Commands.screenshot_selection), desc='scrot selection'),
    Key('S-<Print>', lazy.spawn(Commands.screenshot_all), desc='scrot screen'),
    Key('A-<Print>', lazy.spawn(Commands.screenshot_window), desc='scrot window'),

    # DMENU
    Key("M-r", lazy.run_extension(extension.DmenuRun()), desc='dmenu run'),
    Key("M-A-w", lazy.run_extension(extension.WindowList(
        item_format="{group}: {window}",
        foreground=BLUE,
        selected_background=BLUE)),
        desc='window list'),
    Key("M-C-c", lazy.run_extension(extension.Dmenu(
        dmenu_command="clipmenu",
        foreground=YELLOW,
        selected_background=YELLOW)),
        desc='clipmenu'),
    Key("M-A-p", lazy.run_extension(extension.Dmenu(
        dmenu_command="passmenu",
        foreground=RED,
        selected_background=RED)),
        desc='passmenu'),
    Key("M-A-n", lazy.run_extension(extension.Dmenu(
        dmenu_command="networkmanager_dmenu",
        foreground=RED,
        selected_background=RED)),
        desc='dmenu networking'),
    Key("M-A-m", lazy.run_extension(extension.CommandSet(
        commands={
            'play/pause': '[ $(mocp -i | wc -l) -lt 2 ] && mocp -p || mocp -G',
            'next': 'mocp -f',
            'previous': 'mocp -r',
            'quit': 'mocp -x',
            'open': 'st -e mocp &',
            'shuffle': 'mocp -t shuffle',
            'repeat': 'mocp -t repeat',
            },
        pre_commands=['[ $(mocp -i | wc -l) -lt 1 ] && mocp -S'],
        foreground=BLUE, selected_background=BLUE)),
        desc='dmenu MOC'),
    Key("M-C-q", lazy.run_extension(extension.CommandSet(
        commands={
            'lock': 'slock',
            'suspend': 'systemctl suspend && slock',
            'restart': 'reboot',
            'halt': 'systemctl poweroff',
            'logout': 'qtile-cmd -o cmd -f shutdown',
            'reload': 'qtile-cmd -o cmd -f restart',
            },
        foreground=RED, selected_background=RED)),
        desc='dmenu session manager'),
    Key("M-A-b", lazy.run_extension(extension.CommandSet(
        commands={
            'mail (neomutt)': 'EDITOR=/usr/bin/nvim st -e neomutt &',
            'irc (irssi)': 'st -e irssi &',
            'scan (utsushi)': 'utsushi &',
            },
        foreground=YELLOW, selected_background=YELLOW)),
        desc='dmenu quicklaunch'),
]

groups = [Group(i) for i in "1234567890"]

for i in groups:
    keys.extend([
        Key("M-%s" % i.name, lazy.group[i.name].toscreen()),
        Key("M-S-%s" % i.name, lazy.window.togroup(i.name)),
    ])

layouts = [
    layout.Max(),
    layout.MonadTall(border_focus=RED, new_at_current=True),
    layout.Columns(border_focus=RED),
    layout.Bsp(border_focus=RED),
]

widget_defaults = dict(
    font=FONT,
    fontsize=FONT_SIZE,
    padding=3,
    foreground=WHITE,
    background=BLACK
)
extension_defaults = dict(
    dmenu_prompt=">",
    dmenu_font=FONT + '-8',
    background=BLACK,
    foreground=GREEN,
    selected_background=GREEN,
    selected_foreground=BLACK,
    dmenu_height=24,
)

keyboard_widget = widget.KeyboardLayout(
        configured_keyboards=['us', 'lt sgs', 'ru phonetic'],
        # display_map={
        #     'us': 'us ',
        #     'lt sgs': 'sgs',
        #     # 'ru phonetic': 'ru',
        #     },
        options='compose:menu,grp_led:scroll',
        foreground=GREEN
        )

top = bar.Bar(
    [
        widget.GroupBox(hide_unused=True),
        widget.CurrentLayoutIcon(scale=0.65),
        widget.WindowName(),
        widget.Clipboard(foreground=RED),
        widget.Moc(play_color=GREEN, noplay_color=YELLOW),
        widget.Systray(),

        widget.Volume(
            volume_app=commands.alsamixer,
            foreground=GREEN),

        keyboard_widget,

        widget.Battery(
            discharge_char='↓',
            charge_char='↑',
            format='{char} {hour:d}:{min:02d}',
            foreground=YELLOW,
            low_foreground=RED),

        widget.Maildir(
            maildir_path='~/.local/share/mail/gmail',
            sub_folders=[{'path': 'INBOX', 'label': 'g'}],
            total=True,
            foreground=BLUE),

        widget.Maildir(
            maildir_path='~/.local/share/mail/zordsdavini',
            sub_folders=[{'path': 'INBOX', 'label': 'z'}],
            total=True,
            foreground=BLUE),

        widget.CheckUpdates(
            distro='Arch_yay',
            display_format='{updates}',
            colour_no_update=GREEN,
            colour_have_updates=RED,
            execute=commands.update),

        widget.Clock(format='%Y-%m-%d %H:%M'),
    ],
    24,
)


bottom = bar.Bar(
    [
        widget.Backlight(
            change_command='light -S {0}',
            foreground=GREEN,
            backlight_name='intel_backlight'),

        widget.Pomodoro(
            color_inactive=YELLOW,
            color_break=GREEN,
            color_active=RED),

        widget.GenPollText(
            func=commands.get_watson_status,
            update_interval=1,
            foreground=BLUE),

        widget.Spacer(length=bar.STRETCH),
        widget.CPUGraph(
            line_width=1,
            border_width=0,
            width=66,
            type='box',
            graph_color=RED,
            fill_color=RED
            ),
        widget.NetGraph(
            line_width=1,
            border_width=0,
            width=66,
            type='box',
            graph_color=BLUE,
            fill_color=BLUE,
            interface="auto"),
        widget.MemoryGraph(
            line_width=1,
            border_width=0,
            width=16,
            type='box',
            graph_color=YELLOW,
            fill_color=YELLOW
            ),
    ],
    24,
)
screens = [
    Screen(top=top, bottom=bottom),
    Screen(top=bar.Bar(
        [
            widget.CurrentLayoutIcon(scale=0.65),
            widget.WindowName(),
        ],
        24
    )),
]

# Drag floating layouts.
mouse = [
    Drag(
        ["mod4"],
        "Button1",
        lazy.window.set_position_floating(),
        start=lazy.window.get_position()),

    Drag(
        ["mod4"],
        "Button3",
        lazy.window.set_size_floating(),
        start=lazy.window.get_size()),

    Click(
        ["mod4"],
        "Button2",
        lazy.window.toggle_floating())
]

dgroups_key_binder = None
dgroups_app_rules = []  # type: List
main = None
follow_mouse_focus = True
bring_front_click = False
cursor_warp = False
floating_layout = layout.Floating(float_rules=[
    {'wmclass': 'confirm'},
    {'wmclass': 'dialog'},
    {'wmclass': 'download'},
    {'wmclass': 'error'},
    {'wmclass': 'file_progress'},
    {'wmclass': 'notification'},
    {'wmclass': 'splash'},
    {'wmclass': 'toolbar'},
    {'wmclass': 'confirmreset'},  # gitk
    {'wmclass': 'makebranch'},  # gitk
    {'wmclass': 'maketag'},  # gitk
    {'wname': 'branchdialog'},  # gitk
    {'wname': 'pinentry'},  # GPG key password entry
    {'wmclass': 'ssh-askpass'},  # ssh-askpass
])
auto_fullscreen = True
focus_on_window_activation = "smart"


@hook.subscribe.startup
def startup():
    bottom.show(False)


@hook.subscribe.startup_once
def startup_once():
    commands.reload_screen()


@hook.subscribe.screen_change
def restart_on_randr(qtile, ev):
    commands.reload_screen()
    qtile.cmd_restart()


# XXX: Gasp! We're lying here. In fact, nobody really uses or cares about this
# string besides java UI toolkits; you can see several discussions on the
# mailing lists, GitHub issues, and other WM documentation that suggest setting
# this string if your java app doesn't work correctly. We may as well just lie
# and say that we're a working one by default.
#
# We choose LG3D to maximize irony: it is a 3D non-reparenting WM written in
# java that happens to be on java's whitelist.
wmname = "LG3D"
