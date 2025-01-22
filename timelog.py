# Copyright (c) 2023 Zordsdavini
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

from datetime import datetime, timedelta
from time import time

from libqtile.command.base import expose_command
from libqtile.utils import send_notification
from libqtile.widget import base


class TimeLog(base.ThreadPoolText):
    """Time logging widget.

    Mouse buttons:
        - left: start/pouse
        - middle: restart
        - right: stop (turn off)
        - weel up: increase by minutes
        - weel down: decrease by minutes

    toggle_pause - exported command (can be bind)
    """

    defaults = [
        (
            "update_interval",
            1,
            "Update interval in seconds, if none, the "
            "widget updates whenever the event loop is idle.",
        ),
    ]

    STATUS_INACTIVE = 0
    STATUS_PAUSED = 1
    STATUS_ACTIVE = 2

    status = STATUS_INACTIVE
    collected_time = None
    start_time = None

    def __init__(self, **config):
        base.ThreadPoolText.__init__(self, "", **config)
        self.add_defaults(TimeLog.defaults)

        self.add_callbacks(
            {
                "Button1": self.toggle_pause,
                "Button2": self.restart,
                "Button3": self.inactivate,
                "Button4": self.increase,
                "Button5": self.decrease,
            }
        )


    def tick(self):
        self.update(self.poll())
        return self.update_interval - time() % self.update_interval


    def _get_text(self):
        if self.status == self.STATUS_INACTIVE:
            return u'💤'
        if self.status == self.STATUS_PAUSED:
            return u"⏸ %i:%02d:%02d" % (
                self.collected_time.seconds // 3600,
                self.collected_time.seconds % 3600 // 60,
                self.collected_time.seconds % 60,
            )

        diff = datetime.now() - self.start_time
        diff = self.collected_time + diff if self.collected_time else diff

        return "▶️ %i:%02d:%02d" % (
            diff.seconds // 3600,
            diff.seconds % 3600 // 60,
            diff.seconds % 60,
        )


    def restart(self):
        self.status = self.STATUS_ACTIVE
        self.start_time = datetime.now()
        self.collected_time = None


    @expose_command
    def toggle_pause(self):
        if self.status == self.STATUS_INACTIVE:
            return self.restart()

        if self.status == self.STATUS_ACTIVE:
            self.status = self.STATUS_PAUSED
            diff = datetime.now() - self.start_time
            self.collected_time = self.collected_time + diff if self.collected_time else diff
            return

        self.status = self.STATUS_ACTIVE
        self.start_time = datetime.now()


    def inactivate(self):
        self.status = self.STATUS_INACTIVE
        self.collected_time = None
        self.start_time = None

    def increase(self):
        diff = timedelta(0, 60)
        self.collected_time = self.collected_time + diff if self.collected_time else diff

    def decrease(self):
        diff = timedelta(0, 60)
        self.collected_time = self.collected_time - diff if self.collected_time else timedelta(0)

    def poll(self):
        return self._get_text()
