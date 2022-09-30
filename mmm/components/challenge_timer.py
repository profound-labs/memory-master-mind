#!/usr/bin/env python3

from typing import Callable, Optional

from rich.align import Align
from rich.text import Text

from textual import events
from textual.reactive import Reactive
from textual.widget import Widget

class ChallengeTimer(Widget):
    seconds_remain = Reactive(0)
    timer_count: int = 0
    current_timer_name: Optional[str] = None
    tick_cb: Optional[Callable] = None
    final_cb: Optional[Callable] = None

    def __init__(self):
        super().__init__()
        def noop():
            pass
        self.timers = dict()
        self.timer_count += 1
        k = str(self.timer_count)
        self.current_timer_name = k
        self.set_timer(1, noop, name="x")

    async def on_timer(self, event: events.Timer) -> None:
        if self.current_timer_name is None:
            return

        k = self.current_timer_name
        if event.timer.name == k:
            if self.tick_cb is not None:
                self.tick_cb()

            if self.seconds_remain - 1 <= 0:
                self.seconds_remain = 0
                if self.final_cb is not None:
                    self.final_cb()
            else:
                self.seconds_remain -= 1
                self.set_timer(delay=1, name=k)

    def start_timer(self,
                    secs: int,
                    final_cb: Callable,
                    tick_cb: Optional[Callable] = None):
        self.timer_count += 1
        k = str(self.timer_count)
        self.current_timer_name = k
        self.set_timer(delay=1, name=k)
        self.seconds_remain = secs
        self.final_cb = final_cb
        self.tick_cb = tick_cb

    def stop_timer(self):
        self.seconds_remain = 0
        self.current_timer_name = None

    def render(self):
        if self.seconds_remain > 0:
            text = f"{self.seconds_remain}s "
        else:
            text = ""
        return Align.right(Text(text), vertical="middle", height=1)
