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

import json
import sys
from os import getenv, path
from subprocess import call, check_output
from typing import List  # noqa: F401

import psutil
from libqtile import bar, extension, hook, layout, widget
from libqtile.command.client import CommandClient
from libqtile.config import (Click, Drag, EzKey, Group, Key, KeyChord, Match,
                             Screen)
from libqtile.lazy import lazy
from libqtile.log_utils import logger

logger.debug('Starting...')

"""
TODO
====

2. integrate XF86Tools

improve Qtile:
-------------

2. tooltips
3. mouse clicks to all widgets
6. theme extension

10. save state of windows on restart
11. keyboard layout with flag
12. Hyper-w - web chord:
    b - open dmenu with bookmarks
    d - delfi
    f - firefox
    n - nextcloud
    ....
13. inner border - set inner border on demand to mark window


AUDIO:
    Keyboard volume control
See Keyboard shortcuts#Xorg to bind the following commands to your volume keys: XF86AudioRaiseVolume, XF86AudioLowerVolume and XF86AudioMute.

First find out which sink corresponds to the audio output you would like to control. To list available sinks:

$ pactl list sinks short
Suppose sink 0 is to be used, to raise the volume:

sh -c "pactl set-sink-mute 0 false ; pactl set-sink-volume 0 +5%"
To lower the volume:

$ sh -c "pactl set-sink-mute 0 false ; pactl set-sink-volume 0 -5%"
To mute/unmute the volume:

$ pactl set-sink-mute 0 toggle
To mute/unmute the microphone:

$ pactl set-source-mute 1 toggle

"""


# monadtall extention to follow maximized window if we have only two
@lazy.function
def z_maximize(qtile):
    layout = qtile.current_layout
    group = qtile.current_group

    if layout.name == 'monadtall':
        layout.cmd_maximize()
        if len(group.windows) != 2:
            return

    if layout.name == 'columns':
        # developped for 2 windows...

        if len(group.windows) < 2:
            return

        min_ratio = .25
        layout_width = group.screen.dwidth
        fw = qtile.current_window
        if layout_width/2 < fw.width:
            # minimize
            if fw.x == 0:
                cmd = layout.cmd_grow_left
            else:
                cmd = layout.cmd_grow_right
            while fw.width > layout_width*min_ratio:
                cmd()
        else:
            # maximize
            if fw.x == 0:
                cmd = layout.cmd_grow_right
            else:
                cmd = layout.cmd_grow_left
            while fw.width < layout_width*(1-min_ratio):
                cmd()

    fw = qtile.current_window
    ow = None
    # get other window
    for w in group.windows:
        if w != fw:
            ow = w

    if ow and fw.info()['width'] < ow.info()['width']:
        layout.cmd_next()


def z_update_bar_bg(qtile):
    current_screen = qtile.current_screen
    for screen in qtile.screens:
        bg_color = GREEN if current_screen == screen else RED
        bar = screen.right if screen.right is not None else screen.left
        for w in bar.widgets:
            if 'spacer' == w.name:
                w.background = bg_color
        bar.draw()


terminal = 'alacritty'


class Commands:
    margins = 0
    margin_step = 3

    autorandr = ['autorandr', '-c']
    fehbg = ['sh', '~/.fehbg']
    alsamixer = terminal+' -e alsamixer'
    update = terminal+" -e yay -Syu"
    volume_up = 'amixer -q -c 0 sset Master 5dB+'
    volume_down = 'amixer -q -c 0 sset Master 5dB-'
    volume_toggle = 'amixer -q set Master toggle'
    mic_toggle = 'amixer -q set Dmic0 toggle'
    screenshot_all = 'flameshot full'
    screenshot_selection = 'flameshot gui'
    brightness_up = 'light -A 5'
    brightness_down = 'light -U 5'

    def reload_screen(self):
        call(self.autorandr)
        call(self.fehbg)

    def get_watson_status(self):
        w_stat = check_output(['watson', 'status', '-p'])
        w_stat = w_stat.decode("utf-8").replace('\n', '')
        if w_stat == 'No project started.':
            return w_stat
        output = w_stat + ' '
        w_stat = check_output(['watson', 'status', '-t'])
        output += w_stat.decode("utf-8").replace('\n', '')
        w_stat = check_output(['watson', 'status', '-e'])
        output += ':: '+w_stat.decode("utf-8").replace('\n', '')
        return output

    def get_vpn_status(self):
        nm_out = check_output(['nmcli', 'c', 'show', '--active'])
        for line in nm_out.decode('utf-8').split('\n'):
            if line.find('vpn') >= 0:
                return '(' + line.split(' ')[0] + ')'
            if line.find('wireguard') >= 0:
                return '(' + line.split(' ')[0] + ')'
        return ''

    def get_neopay_branch(self):
        branch_name = check_output(
                'git symbolic-ref --short -q HEAD',
                cwd='/home/arnas/src/neopay/www/neopay',
                shell=True)

        return branch_name.decode("utf-8").replace('\n', '')

    def get_ss_branch(self):
        branch_name = check_output(
                'git symbolic-ref --short -q HEAD',
                cwd='/home/arnas/src/neopay/www/mano',
                shell=True)

        return branch_name.decode("utf-8").replace('\n', '')

    def get_admin_branch(self):
        branch_name = check_output(
                'git symbolic-ref --short -q HEAD',
                cwd='/home/arnas/src/neopay/www/admin',
                shell=True)

        return branch_name.decode("utf-8").replace('\n', '')

    def get_keyboard(self):
        display_map = {
            'us': 'us ',
            'lt(sgs)': 'sgs',
            'ru(phonetic)': 'ru ',
            }
        keyboard = check_output(
                'xkb-switch -p',
                shell=True).decode('utf-8').replace('\n', '')

        return display_map[keyboard]

    def get_margins(self):
        return self.margins

    def increase_margins(self):
        self.margins += self.margin_step

    def decrease_margins(self):
        self.margins -= self.margin_step
        if self.margins < 0:
            self.margins = 0


commands = Commands()


@lazy.function
def z_increase_margins(qtile):
    commands.increase_margins()
    qtile.current_layout.margin = commands.get_margins()


@lazy.function
def z_decrease_margins(qtile):
    commands.decrease_margins()
    qtile.current_layout.margin = commands.get_margins()


try:
    import xrp  # pip install xparser
    xresources = path.realpath(getenv('HOME') + '/.Xresources')
    result = xrp.parse_file(xresources, 'utf-8')
    font_data = result.resources['*.font'].split(':')
    FONT = font_data[0]
    FONT_SIZE = int(font_data[1].split('=')[1])

    color_data = json.loads(open(getenv('HOME')+'/.cache/wal/colors.json').read())
except Exception:
    logger.debug('Xresources load failed', exc_info=True)
    FONT = 'Hack Nerd Font'
    FONT_SIZE = 14
    color_data = {
            'colors': {
                "color0": "#32302f",
                "color1": "#fb4934",
                "color2": "#b8bb26",
                "color3": "#fabd2f",
                "color4": "#83a598",
                "color5": "#d3869b",
                "color6": "#8ec07c",
                "color7": "#d5c4a1",
                "color8": "#665c54",
                "color9": "#fb4934",
                "color10": "#b8bb26",
                "color11": "#fabd2f",
                "color12": "#83a598",
                "color13": "#d3869b",
                "color14": "#8ec07c",
                "color15": "#fbf1c7"
                }
            }

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

hyper = 'mod3'
keys = [
    # Switch between windows
    EzKey("M-h", lazy.layout.left()),
    EzKey("M-l", lazy.layout.right()),
    EzKey("M-j", lazy.layout.down()),
    EzKey("M-k", lazy.layout.up()),

    # Move windows
    EzKey("M-S-h", lazy.layout.shuffle_left()),
    EzKey("M-S-l", lazy.layout.shuffle_right()),
    EzKey("M-S-j", lazy.layout.shuffle_down()),
    EzKey("M-S-k", lazy.layout.shuffle_up()),

    # Grow windows
    EzKey("M-C-h", lazy.layout.grow_left()),
    EzKey("M-C-l", lazy.layout.grow_right()),
    EzKey("M-C-j", lazy.layout.grow_down()),
    EzKey("M-C-k", lazy.layout.grow_up()),

    # Flip windows
    EzKey("M-A-h", lazy.layout.flip_left()),
    EzKey("M-A-l", lazy.layout.flip_right()),
    EzKey("M-A-j", lazy.layout.flip_down()),
    EzKey("M-A-k", lazy.layout.flip_up()),

    EzKey("M-S-<Return>", lazy.layout.toggle_split()),

    # Monadtall additional
    EzKey("M-i", lazy.layout.grow()),
    EzKey("M-m", lazy.layout.shrink()),
    EzKey("M-o", z_maximize, desc='maximize window'),
    EzKey("M-n", lazy.layout.normalize(), desc='reset layout'),
    EzKey("M-S-<space>", lazy.layout.flip()),

    # Switch window focus to other pane(s) of stack
    EzKey("M-<space>", lazy.layout.next(), desc='next window'),

    # Focus screen
    EzKey("M-<comma>", lazy.prev_screen()),
    EzKey("M-<period>", lazy.next_screen()),

    EzKey("M-<Return>", lazy.spawn(terminal)),

    EzKey(
        "A-<space>",
        lazy.widget['keyboardlayout'].next_keyboard(),
        desc='switch keyboard layout'),

    EzKey("M-<Tab>", lazy.next_layout()),
    EzKey("M-S-w", lazy.window.kill(), desc='close window'),
    EzKey("M-C-w", lazy.spawn('xkill'), desc='kill window'),

    EzKey("M-S-x", lazy.hide_show_bar("top"), desc='toggle top bar'),
    EzKey("M-C-x", lazy.hide_show_bar("bottom"), desc='toggle bottom bar'),

    EzKey("M-C-r", lazy.restart()),
    EzKey("M-C-f", lazy.window.toggle_floating()),

    # Sound
    EzKey('<XF86AudioRaiseVolume>', lazy.spawn(Commands.volume_up)),
    EzKey('<XF86AudioLowerVolume>', lazy.spawn(Commands.volume_down)),
    EzKey('M-<Up>', lazy.spawn(Commands.volume_up)),
    EzKey('M-<Down>', lazy.spawn(Commands.volume_down)),
    EzKey('<XF86AudioMute>', lazy.spawn(Commands.volume_toggle)),
    EzKey('<XF86AudioMicMute>', lazy.spawn(Commands.mic_toggle)),

    # Other FN keys
    EzKey('<XF86MonBrightnessUp>', lazy.spawn(Commands.brightness_up)),
    EzKey('<XF86MonBrightnessDown>', lazy.spawn(Commands.brightness_down)),
    EzKey('<XF86Display>', lazy.spawn('arandr')),

    EzKey(
        '<XF86Favorites>',
        lazy.spawn('touchpad_toggle'),
        desc='on/off touchpad'),

    # Screenshot
    EzKey(
        '<Print>',
        lazy.spawn(Commands.screenshot_selection),
        desc='screenshot all'),

    EzKey(
        'S-<Print>',
        lazy.spawn(Commands.screenshot_all),
        desc='screenshot'),

    # Quick lounch
    EzKey("M-v", lazy.spawn(terminal+" -e nvim"), desc="ViM"),
    EzKey("M-w", lazy.spawn("google-chrome-stable"), desc="chrome"),
    EzKey("M-f", lazy.spawn(terminal+" -e ranger"), desc="ranger"),
    EzKey("M-c", lazy.spawn(terminal+" -e bc -l"), desc="calculator (bc)"),

    # DMENU
    EzKey("M-r", lazy.run_extension(extension.DmenuRun()), desc='dmenu run'),
    EzKey("M-A-w", lazy.run_extension(extension.WindowList(
        item_format="{group}: {window}",
        foreground=BLUE,
        selected_background=BLUE)),
        desc='window list'),
    EzKey("M-C-c", lazy.run_extension(extension.Dmenu(
        dmenu_command="clipmenu",
        foreground=YELLOW,
        selected_background=YELLOW)),
        desc='clipmenu'),
    EzKey("M-A-p", lazy.run_extension(extension.Dmenu(
        dmenu_command="passmenu",
        foreground=RED,
        selected_background=RED,
        dmenu_lines=50)),
        desc='passmenu'),
    EzKey("M-A-n", lazy.run_extension(extension.Dmenu(
        dmenu_command="networkmanager_dmenu",
        foreground=RED,
        selected_background=RED)),
        desc='dmenu networking'),
    EzKey("M-A-m", lazy.run_extension(extension.CommandSet(
        commands={
            'play/pause': '[ $(mocp -i | wc -l) -lt 2 ] && mocp -p || mocp -G',
            'next': 'mocp -f',
            'previous': 'mocp -r',
            'quit': 'mocp -x',
            'open': terminal+' -e mocp &',
            'shuffle': 'mocp -t shuffle',
            'repeat': 'mocp -t repeat',
            },
        pre_commands=['[ $(mocp -i | wc -l) -lt 1 ] && mocp -S'],
        foreground=BLUE, selected_background=BLUE)),
        desc='dmenu MOC'),
    KeyChord([hyper], "m", [
        Key([], "z", lazy.spawn("mocp -r")),
        Key([], "x", lazy.spawn("mocp -p")),
        Key([], "c", lazy.spawn("mocp -G")),
        Key([], "v", lazy.spawn("mocp -s")),
        Key([], "b", lazy.spawn("mocp -f")),
        ]),
    EzKey("M-C-q", lazy.run_extension(extension.CommandSet(
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
    EzKey("M-A-r", lazy.run_extension(extension.CommandSet(
        commands={
            'mail (neomutt)': 'EDITOR=/usr/bin/nvim '+terminal+' -e neomutt &',
            'irc (irssi)': terminal+' -e irssi &',
            'scan (utsushi)': 'utsushi &',
            },
        foreground=YELLOW, selected_background=YELLOW)),
        desc='dmenu quicklaunch'),

    EzKey("M-A-i", lazy.run_extension(extension.CommandSet(
        commands={
            'work today': 'notify-send -u low -t 10000 "🛈" '
            '"`watson report -Gdc`"',
            'work log': 'notify-send -u low -t 10000 "🛈" '
            '"`watson log --from=$(date  --date=\"5 days ago\" +"%Y-%m-%d") -Gc`"',
            'time': 'notify-send -u normal -t 30000 "🛈" '
            '"`LC_ALL=sgs_LT.utf-8 date && echo && LC_ALL=sgs_LT.utf-8 cal`"',
            'weather':  'notify-send -u critical -t 10000 "🛈" '
            '"`ansiweather -l Galgiai -a 0 -s true -i 0 -p 0 -d true && echo '
            '&& ansiweather -l Galgiai -f 7 -a false -s true`"',
            'uptime': 'notify-send -u low "🛈" "`uptime -p`"',
            'kernel': 'notify-send -u low "🛈" "`uname -r`"',
            'battery': 'notify-send -u low "🛈" "`upower -i /org/freedesktop/UPower/devices/battery_BAT0`"',
            },
        foreground=BLUE, selected_background=BLUE)),
        desc='dmenu various info'),
    EzKey("M-A-t", lazy.spawn('watson_dmenu'), desc='watson dmenu'),
    Key([hyper], "j", z_decrease_margins),
    Key([hyper], "k", z_increase_margins),
    EzKey("C-M-A-j", z_decrease_margins),
    EzKey("C-M-A-k", z_increase_margins),
]

groups = [Group(i) for i in "1234567890"]
sgs_groups = {
    '1': 'aogonek',
    '2': 'ccaron',
    '3': 'eogonek',
    '4': 'eabovedot',
    '5': 'iogonek',
    '6': 'scaron',
    '7': 'uogonek',
    '8': 'umacron',
    '9': 'doublelowquotemark',
    '0': 'leftdoublequotemark'
    }

for i in groups:
    keys.extend([
        EzKey("M-%s" % i.name, lazy.group[i.name].toscreen(toggle=True)),
        EzKey("M-S-%s" % i.name, lazy.window.togroup(i.name)),

        EzKey("M-<%s>" % sgs_groups[i.name], lazy.group[i.name].toscreen(toggle=True)),
        EzKey("M-S-<%s>" % sgs_groups[i.name], lazy.window.togroup(i.name)),
    ])

layouts = [
    layout.Columns(border_focus=RED, margin=0),
    layout.Max(),
    # layout.MonadTall(border_focus=RED, new_at_current=True),
]

widget_defaults = dict(
    font=FONT,
    fontsize=FONT_SIZE,
    padding=3,
    foreground=WHITE,
    background=BLACK
)
extension_defaults = dict(
    dmenu_font=FONT + '-10',
    background=BLACK,
    foreground=GREEN,
    selected_background=GREEN,
    selected_foreground=BLACK,
    dmenu_height=24,
)

try:
    # import passwords
    cloud = path.realpath(getenv('HOME') + '/cloud')
    sys.path.insert(1, cloud)
    import pakavuota

    logger.info(pakavuota.gmail_user)
    gmail_widget = widget.GmailChecker(
            username=pakavuota.gmail_user,
            password=pakavuota.gmail_password,
            status_only_unseen=True,
            display_fmt="{0}",
            foreground=YELLOW)
except Exception:
    gmail_widget = widget.TextBox(text='GMAIL', foreground=RED)


top = bar.Bar(
    [
        widget.GroupBox(hide_unused=True),
        widget.CurrentLayoutIcon(scale=0.65),
        widget.WindowName(foreground=GREEN),
        widget.Clipboard(foreground=RED),
        widget.Moc(play_color=GREEN, noplay_color=YELLOW),

        widget.PulseVolume(
            foreground=BLUE),

        # widget.Volume(
        #     volume_app=commands.alsamixer,
        #     foreground=GREEN),

        # widget.KeyboardLayout(
        #     configured_keyboards=['us', 'lt sgs', 'ru phonetic'],
        #     display_map={
        #         'us': 'us ',
        #         'lt sgs': 'sgs',
        #         'ru phonetic': 'ru ',
        #         },
        #     options='compose:rctrl,lv3:ralt_switch',
        #     foreground=GREEN
        #     ),
        # widget.KeyboardLayout(
            # layout_groups='us,lt,ru',
            # variant='intl,sgs,phonetic',
            # display_map={
            #     'us': 'us ',
            #     'lt sgs': 'sgs',
            #     'ru phonetic': 'ru ',
            #     },
            # options='grp:ctrl_shift_toggle,compose:rctrl,lv3:ralt_switch',
            # config_file='~/.config/keyboard',
        widget.GenPollText(
            func=commands.get_keyboard,
            update_interval=0.5,
            foreground=GREEN
            ),

        gmail_widget,

        widget.Maildir(
            maildir_path='~/.local/share/mail/zordsdavini',
            sub_folders=[{'path': 'INBOX', 'label': 'z'}],
            total=True,
            subfolder_fmt='{label} {value}',
            hide_when_empty=True,
            update_interval=10,
            foreground=BLUE),

        widget.CheckUpdates(
            distro='Arch_yay',
            display_format='{updates}',
            colour_no_update=GREEN,
            colour_have_updates=RED,
            execute=commands.update),

        widget.Clock(format='%Y-%m-%d %H:%M', foreground=BLACK, background=BLUE),
        widget.Systray(),
    ],
    24,
    opacity=0.6
)


bottom = bar.Bar(
    [
        # widget.Pomodoro(
        #     num_pomodori=4,
        #     length_pomodori=25,
        #     length_short_break=5,
        #     length_long_break=15,
        #     color_inactive=YELLOW,
        #     color_break=GREEN,
        #     color_active=RED,
        #     notification_on=True,
        #     prefix_inactive="🍅",
        #     prefix_active="🍅 ",
        #     prefix_break="☕ ",
        #     prefix_long_break="☕ ",
        #     prefix_paused="🍅 PAUSED",
        #     ),

        widget.GenPollText(
            func=commands.get_watson_status,
            update_interval=2,
            foreground=BLUE),

        # widget.GenPollText(
        #     func=commands.get_neopay_branch,
        #     update_interval=2,
        #     foreground=RED),

        # widget.GenPollText(
        #     func=commands.get_ss_branch,
        #     update_interval=2,
        #     foreground=YELLOW),

        # widget.GenPollText(
        #     func=commands.get_admin_branch,
        #     update_interval=2,
        #     foreground=MAGENTA),

        widget.Spacer(length=bar.STRETCH),

        widget.Battery(
            discharge_char='↓',
            charge_char='↑',
            format='{char} {hour:d}:{min:02d}',
            foreground=MAGENTA,
            low_foreground=RED),

        widget.Backlight(
            change_command='light -S {0}',
            background=YELLOW,
            foreground=BLACK,
            backlight_name='intel_backlight'),

        widget.Wlan(
            interface='wlp0s20f3',
            format='{essid} {percent:2.0%}',
            background=BLUE,
            foreground=BLACK),

        widget.GenPollText(
            func=commands.get_vpn_status,
            update_interval=2,
            background=BLUE,
            foreground=BLACK),

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
            border_width=1,
            width=4,
            type='box',
            graph_color=YELLOW,
            fill_color=YELLOW
            ),
    ],
    24,
    opacity=0.6
)

screens = [
    Screen(
        top=top,
        bottom=bottom,
        right=bar.Bar(
            [widget.Spacer(length=bar.STRETCH)],
            4,
            opacity=0.6),
        wallpaper='/home/arnas/cloud/configs/arch-linux-wallpaper.jpg',
        wallpaper_mode='fill'
    ),
    Screen(top=bar.Bar(
        [
            widget.CurrentLayoutIcon(scale=0.65),
            widget.WindowName(foreground=GREEN),
        ],
        24,
        opacity=0.6,
        background=RED,
        ),
        left=bar.Bar(
            [widget.Spacer(length=bar.STRETCH)],
            4,
            opacity=0.6),
        wallpaper='/home/arnas/cloud/configs/arch-linux-wallpaper.jpg',
        wallpaper_mode='fill'
    ),
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
bring_front_click = True
cursor_warp = False

floating_layout = layout.Floating(
    float_rules=[
        *layout.Floating.default_float_rules,
        Match(wm_class='confirmreset'),  # gitk
        Match(wm_class='makebranch'),  # gitk
        Match(wm_class='maketag'),  # gitk
        Match(wm_class='ssh-askpass'),  # ssh-askpass
        Match(title='branchdialog'),  # gitk
        Match(title='pinentry'),  # GPG key password entry
        Match(title='pinentry-gtk-2'),  # GPG key password entry
    ],
    border_focus=GREEN)

auto_fullscreen = True
focus_on_window_activation = "smart"


@hook.subscribe.startup
def startup():
    # bottom.show(False)
    pass


@hook.subscribe.startup_once
def startup_once():
    commands.reload_screen()


@hook.subscribe.screen_change
def restart_on_randr(qtile, ev):
    commands.reload_screen()
    qtile.cmd_restart()
    z_update_bar_bg(qtile)


@hook.subscribe.client_new
def floating_size_hints(window):
    hints = window.window.get_wm_normal_hints()
    if hints and 0 < hints['max_width'] < 1000:
        window.floating = True


@hook.subscribe.client_focus
def activate_screen_on_mouse_enter(window):
    qtile = window.group.screen.qtile
    window_screen = window.group.screen
    current_screen = qtile.current_screen

    z_update_bar_bg(qtile)
    if current_screen != window_screen:
        window.focus(False)
        window.group.focus(window, False)


# @hook.subscribe.client_new
# def _swallow(window):
#     pid = window.window.get_net_wm_pid()
#     ppid = psutil.Process(pid).ppid()
#     cpids = {c.window.get_net_wm_pid(): wid for wid, c in window.qtile.windows_map.items()}
#     for i in range(5):
#         if not ppid:
#             return
#         if ppid in cpids:
#             parent = window.qtile.windows_map.get(cpids[ppid])
#             parent.minimized = True
#             window.parent = parent
#             return
#         ppid = psutil.Process(ppid).ppid()


# @hook.subscribe.client_killed
# def _unswallow(window):
#     if hasattr(window, 'parent'):
#         window.parent.minimized = False

# XXX: Gasp! We're lying here. In fact, nobody really uses or cares about this
# string besides java UI toolkits; you can see several discussions on the
# mailing lists, GitHub issues, and other WM documentation that suggest setting
# this string if your java app doesn't work correctly. We may as well just lie
# and say that we're a working one by default.
#
# We choose LG3D to maximize irony: it is a 3D non-reparenting WM written in
# java that happens to be on java's whitelist.
wmname = "Qtile"
