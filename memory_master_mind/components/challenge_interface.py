#!/usr/bin/env python3

import json

from textual import events
from textual.views._grid_view import GridView

from memory_master_mind.components.challenge_timer import ChallengeTimer
from memory_master_mind.components.footer import Footer
from memory_master_mind.components.input_answer import InputAnswer
from memory_master_mind.components.preferences_interface import PreferencesInterface
from memory_master_mind.components.show_challenge_interface import ShowChallengeInterface

import memory_master_mind.db as db
from memory_master_mind.types import QuotesId, Settings, State, load_settings
from memory_master_mind.components.header import Header


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
        self.footer.ch_per_level = d["ch_per_level"]
        self.footer.ch_per_current_level = self.ch_per_current_level + 1

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
                answer = self.show_numbers.format_answer_plain()
                self.log(answer)
                self.state = self.input_answer.check_answer(answer)

                if self.state == State.CORRECT:
                    self.incr_level()
                    self.show_numbers.show_numbers = True
                    self.footer.show_answer = False
                    self.input_answer.end_challenge()
                    self.app.save_stats() # type: ignore

                if self.state == State.WRONG:
                    self.decr_level()
                    self.first_try = False
                    if not self.input_answer.only_numbers:
                        self.set_menu_enabled(False)

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
