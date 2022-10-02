#!/usr/bin/env python3

# Diffuculty level sules:
#
# - Correct answer on first try: increase level.
# - Wrong answer on first try, but correct answer eventually: stay on same level.
# - Show correct answer: decrease level.
# - New challenge without correct answer: decrease level.

from typing import List, Optional, TypedDict
import json

from textual import events
from textual.views._grid_view import GridView

from mmm.components.challenge_timer import ChallengeTimer
from mmm.components.footer import Footer
from mmm.components.input_answer import InputAnswer
from mmm.components.preferences_interface import PreferencesInterface
from mmm.components.show_challenge_interface import ShowChallengeInterface

import mmm.db as db
from mmm.types import QuotesId, State
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
    words_max: int
    quotes_path: str
    last_quote_idx: int


def default_settings(view_id: Optional[str] = None) -> Settings:
    d = Settings(
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
        words_max = 999,
        quotes_path = "",
        last_quote_idx = 0,
    )

    if view_id is not None and view_id == QuotesId:
        d['ch_per_level'] = 1
        d['level_max'] = 10

    return d

def load_settings(view_id: str) -> Settings:
    res = db.get_settings(view_id)
    if res:
        d: Settings = json.loads(res[2])
        return d
    else:
        d = default_settings(view_id)
        s = json.dumps(d)
        db.save_settings(view_id, s)
        return d


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
    show_challenge_blocks_keys: bool = False
    is_text_challenge: bool = False
    help_md_filename: str

    def init_attr(self):
        """Assign self.view_id and self.help_md_filename"""
        raise NotImplementedError

    def init_components(self):
        raise NotImplementedError

    def __init__(self):
        super().__init__()

        self.init_attr()

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
        if self.is_text_challenge:
            self.set_menu_enabled(False)
        self.show_numbers.show_numbers = False
        self.footer.show_answer = True
        self.upd_state(State.STARTED_ANSWER)

    def start_timer(self, seconds_per_level: int):
        self.challenge_timer.stop_timer()
        if seconds_per_level != 0:
            secs = seconds_per_level * self.current_level
            self.challenge_timer.start_timer(
                secs=secs,
                final_cb=self.do_started_answer,
            )

    def new_challenge(self, regenerate: bool = True):
        d = load_settings(self.view_id)
        self.current_level = d["level"]
        self.footer.level = self.current_level
        self.first_try = True

        if self.view_id != QuotesId:
            self.start_timer(d['seconds_per_level'])

        self.show_numbers.new_challenge(regenerate)

        if self.view_id == QuotesId:
            self.show_numbers.show_numbers = False
        else:
            self.show_numbers.show_numbers = True

        self.input_answer.new_challenge()

        if self.view_id == QuotesId:
            self.footer.show_answer = True
            self.set_menu_enabled(False)
            self.upd_state(State.STARTED_ANSWER)
        else:
            self.footer.show_answer = False
            self.set_menu_enabled(True)
            self.upd_state(State.SHOW_CHALLENGE)

    def toggle_menu(self):
        self.app.toggle_menu() # type: ignore
        self.footer.menu_enabled = self.app.menu_enabled # type: ignore

    def menu_enabled(self) -> bool:
        return self.app.menu_enabled # type: ignore

    def set_menu_enabled(self, x: bool):
        self.app.menu_enabled = x # type: ignore
        self.footer.menu_enabled = x # type: ignore

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            return

        if event.key == "ctrl+i":
            if not self.input_answer.only_numbers:
                self.toggle_menu()
            return

        if event.key == "r" and self.menu_enabled():
            if self.state == State.STARTED_ANSWER:
                self.decr_level()
            self.new_challenge(regenerate=False)
            return

        if event.key == "n" and self.menu_enabled():
            if self.state == State.STARTED_ANSWER:
                self.decr_level()
            self.new_challenge()
            return

        if event.key == "s" and self.footer.show_answer and self.menu_enabled():
            self.decr_level()
            self.challenge_timer.stop_timer()
            self.show_numbers.show_numbers = True
            self.upd_state(State.SHOW_ANSWER)
            return

        # Key press after show answer.
        if self.state == State.SHOW_ANSWER:
            self.new_challenge()
            return

        if self.state is State.SHOW_CHALLENGE and self.show_challenge_blocks_keys:
            return

        if self.state in [State.SHOW_CHALLENGE, State.WRONG]:
            self.challenge_timer.stop_timer()
            self.state = State.STARTED_ANSWER
            self.footer.show_answer = True

        if self.state in [State.STARTED_ANSWER, State.WRONG]:
            self.show_numbers.show_numbers = False

            if event.key == "enter" and self.menu_enabled():
                answers = self.show_numbers.format_answers(False)
                self.state = self.input_answer.check_answer(answers)

        if self.state == State.WRONG:
            self.decr_level()
            self.first_try = False
            if not self.input_answer.only_numbers:
                self.set_menu_enabled(False)

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
        self.grid.add_column("col")
        self.grid.add_row("r1", fraction=2)
        self.grid.add_row("r2", size=1)
        self.grid.add_row("r3", fraction=1)
        self.grid.add_row("r4", size=1)

        self.grid.add_areas(show="col,r1")
        self.grid.add_areas(timer="col,r2")
        self.grid.add_areas(answer="col,r3")
        self.grid.add_areas(footer="col,r4")

        self.grid.add_widget(self.show_numbers, area="show")

        if self.view_id != QuotesId:
            self.grid.add_widget(self.challenge_timer, area="timer")

        self.grid.add_widget(self.input_answer, area="answer")
        self.grid.add_widget(self.footer, area="footer")

        self.new_challenge()
