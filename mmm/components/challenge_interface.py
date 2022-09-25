#!/usr/bin/env python3

# Diffuculty level sules:
#
# - Correct answer on first try: increase level.
# - Wrong answer on first try, but correct answer eventually: stay on same level.
# - Show correct answer: decrease level.
# - New challenge without correct answer: decrease level.

from typing import Callable, List, Optional, TypedDict
import json

from rich.align import Align
from rich.text import Text

from textual import events
from textual.reactive import Reactive
from textual.widget import Widget
from textual.views._grid_view import GridView
from mmm.components.footer import Footer
from mmm.components.input_answer import InputAnswer
from mmm.components.preferences_interface import PreferencesInterface

import mmm.db as db
from mmm.types import State
from mmm.components.header import Header

class Settings(TypedDict):
    digits_min: int
    digits_max: int
    ch_per_level: int
    seconds_per_level: int
    level: int
    level_max: int
    zero_padded: bool
    operations: List[str]
    negatives: bool
    solve_frac_dec: int

def default_settings() -> Settings:
    return Settings(
        digits_min = 1,
        digits_max = 2,
        ch_per_level = 2,
        seconds_per_level = 5,
        level = 2,
        level_max = 999,
        zero_padded = False,
        operations = ["+", "-"],
        negatives = False,
        solve_frac_dec = 1,
    )

def load_settings(view_id: str) -> Settings:
    res = db.get_settings(view_id)
    if res:
        d: Settings = json.loads(res[2])
        return d
    else:
        d = default_settings()
        s = json.dumps(d)
        db.save_settings(view_id, s)
        return d

class ChallengeTimer(Widget):
    seconds_remain = Reactive(0)
    timer_count: int = 0
    current_timer_name: Optional[str] = None
    callback: Optional[Callable] = None

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
            if self.seconds_remain == 0:
                if self.callback is not None:
                    self.callback()
            else:
                self.seconds_remain -= 1
                self.set_timer(delay=1, name=k)

    def start_timer(self, secs: int, callback: Callable):
        self.timer_count += 1
        k = str(self.timer_count)
        self.current_timer_name = k
        self.set_timer(delay=1, name=k)
        self.seconds_remain = secs
        self.callback = callback

    def stop_timer(self):
        self.seconds_remain = 0
        self.current_timer_name = None

    def render(self):
        if self.seconds_remain > 0:
            text = f"{self.seconds_remain}s "
        else:
            text = ""
        return Align.right(Text(text), vertical="middle", height=1)

class ShowChallengeInterface(Widget):
    state = Reactive(State.SHOW_CHALLENGE)
    view_id: str
    items = Reactive([])
    show_numbers = Reactive(True)

    def __init__(self, view_id: str):
        super().__init__()
        self.view_id = view_id

    def new_challenge(self):
        raise NotImplementedError

    def format_challenge(self) -> str:
        raise NotImplementedError

    def generate_answer(self) -> str:
        raise NotImplementedError

    def format_answer(self, answer: str, for_display: bool) -> str:
        if for_display:
            return "\n= " + answer
        else:
            return answer

    def on_mount(self):
        self.new_challenge()

    def render(self):
        text = self.format_challenge()
        answer = self.generate_answer()
        if self.state in [State.SHOW_ANSWER, State.CORRECT] and text != answer:
            text += self.format_answer(answer, True)
        return Align.center(Text(text), vertical="middle")


class ChallengeInterface(GridView):
    view_id: str
    state: State = State.SHOW_CHALLENGE
    app_settings: Settings
    show_numbers: ShowChallengeInterface
    challenge_timer: ChallengeTimer
    input_answer: InputAnswer
    header: Header
    footer: Footer
    preferences_view: PreferencesInterface
    current_level: int
    ch_per_current_level: int
    first_try: bool

    def init_view_id(self):
        raise NotImplementedError

    def init_components(self):
        raise NotImplementedError

    def __init__(self):
        super().__init__()

        self.init_view_id()

        d = load_settings(self.view_id)
        self.current_level = d["level"]
        self.ch_per_current_level = 0
        self.first_try = True

        self.challenge_timer = ChallengeTimer()

        self.init_components()

    def get_instruction(self) -> str:
        raise NotImplementedError

    def get_preferences_view(self):
        raise NotImplementedError

    async def focus_input(self):
        await self.input_answer.focus()

    def upd_state(self, value: State) -> None:
        self.state = value
        self.show_numbers.state = value
        self.input_answer.state = value

    def incr_level(self):
        d = load_settings(self.view_id)
        if self.first_try:
            self.ch_per_current_level += 1
            lvl = self.current_level + 1
            if lvl <= d['level_max'] and self.ch_per_current_level >= d['ch_per_level']:
                self.ch_per_current_level = 0
                d['level'] = lvl
        else:
            self.ch_per_current_level = 0
            d['level'] = self.current_level
        db.save_settings(self.view_id, json.dumps(d))

    def decr_level(self):
        if self.current_level <= 1:
            return
        self.ch_per_current_level = 0
        d = load_settings(self.view_id)
        d['level'] = self.current_level - 1
        db.save_settings(self.view_id, json.dumps(d))

    def do_started_answer(self):
        self.show_numbers.show_numbers = False
        self.footer.show_answer = True
        self.upd_state(State.STARTED_ANSWER)

    def new_challenge(self):
        d = load_settings(self.view_id)
        self.current_level = d["level"]
        self.footer.level = self.current_level
        self.first_try = True

        self.challenge_timer.stop_timer()
        if d['seconds_per_level'] != 0:
            secs = d['seconds_per_level'] * self.current_level
            self.challenge_timer.start_timer(secs, self.do_started_answer)

        self.show_numbers.new_challenge()
        self.show_numbers.show_numbers = True

        self.input_answer.new_challenge()

        self.footer.show_answer = False
        self.upd_state(State.SHOW_CHALLENGE)

    def on_key(self, event: events.Key) -> None:
        if event.key in ["ctrl+i", "escape"]:
            return

        # Key press after show answer.
        if self.state == State.SHOW_ANSWER:
            self.new_challenge()
            return

        if event.key == "n":
            if self.state == State.STARTED_ANSWER:
                self.decr_level()
            self.new_challenge()
            return

        if event.key == "s" and self.footer.show_answer:
            self.decr_level()
            self.challenge_timer.stop_timer()
            self.show_numbers.show_numbers = True
            self.upd_state(State.SHOW_ANSWER)
            return

        if self.state in [State.SHOW_CHALLENGE, State.WRONG]:
            self.challenge_timer.stop_timer()
            self.state = State.STARTED_ANSWER
            self.footer.show_answer = True

        if self.state in [State.STARTED_ANSWER, State.WRONG]:
            self.show_numbers.show_numbers = False

            if event.key == "enter":
                s = self.show_numbers.generate_answer()
                answer = self.show_numbers.format_answer(s, False)
                self.state = self.input_answer.check_answer(answer)

        if self.state == State.WRONG:
            self.decr_level()
            self.first_try = False

        if self.state == State.CORRECT:
            self.incr_level()
            self.show_numbers.show_numbers = True
            self.footer.show_answer = False
            self.input_answer.end_challenge()

        self.upd_state(self.state)

    async def on_mount(self) -> None:
        await self.input_answer.focus()

        self.grid.set_align("center", "center")
        self.grid.set_gap(0, 0)
        self.grid.add_column("column")
        self.grid.add_row("row1")
        self.grid.add_row("row2", size=1)
        self.grid.add_row("row3")
        self.grid.add_row("row4", size=1)

        self.grid.add_widget(self.show_numbers)
        self.grid.add_widget(self.challenge_timer)
        self.grid.add_widget(self.input_answer)
        self.grid.add_widget(self.footer)

        self.new_challenge()
