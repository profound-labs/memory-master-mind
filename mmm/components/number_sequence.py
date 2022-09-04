#!/usr/bin/env python3

import re
from random import randrange
from enum import Enum
from typing import TypedDict
import json

from rich.align import Align
from rich.console import RenderableType
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from textual import events
from textual.reactive import Reactive
from textual.widget import Widget
from textual.views._grid_view import GridView

from mmm.db import add_settings, get_settings

CHALLENGE_ID = 'number_sequence'

class AppSettings(TypedDict):
    range_from: int
    range_to: int
    seq_length: int

def default_settings() -> AppSettings:
    return AppSettings(
        range_from = 0,
        range_to = 99,
        seq_length = 2,
    )

def load_settings() -> AppSettings:
    res = get_settings(CHALLENGE_ID)
    if res:
        d: AppSettings = json.loads(res[2])
        return d
    else:
        d = default_settings()
        s = json.dumps(d)
        add_settings(CHALLENGE_ID, s)
        return d

class AppState(int, Enum):
    SHOW_NUMBERS = 0
    STARTED_ANSWER = 1
    CORRECT = 2
    WRONG = 3

class InputNumbers(Widget):
    content = Reactive("")
    input_state = Reactive(AppState.SHOW_NUMBERS)

    def on_key(self, event: events.Key) -> None:
        if self.input_state == AppState.CORRECT:
            return

        if event.key == "ctrl+h":
            self.content = self.content[:-1]
        elif re.search(r'[0-9 ]', event.key):
                self.content += event.key

    def check_answer(self, correct_answer: str):
        if self.content.strip() == correct_answer:
            self.input_state = AppState.CORRECT
        else:
            self.input_state = AppState.WRONG

        return self.input_state

    def render(self) -> RenderableType:
        s = self.content + "_"
        renderable = Align.left(Text(s, style="bold"))

        title = "Memorize, then type it."

        if self.input_state == AppState.STARTED_ANSWER:
            style = "bold white on rgb(50,57,50)"
            border_style = Style(color="yellow")

        elif self.input_state == AppState.CORRECT:
            title = "Correct!"
            style = "bold white on rgb(50,57,50)"
            border_style = Style(color="green")

        elif self.input_state == AppState.WRONG:
            style = "bold white on rgb(50,57,50)"
            border_style = Style(color="red")

        else:
            # AppState.SHOW_NUMBERS
            style = "white on rgb(50,57,50)"
            border_style = Style(color="white")

        return Panel(
            renderable,
            title=title,
            title_align="center",
            style=style,
            border_style=border_style,
        )


class ShowNumbers(Widget):
    items = Reactive([])
    show_numbers = Reactive(True)

    def new_challenge(self):
        d = load_settings()
        a = []
        for _ in range(0, d['seq_length']):
            n = randrange(d['range_from'], d['range_to'])
            a.append(str(n))
        self.items = a

    def on_mount(self):
        self.new_challenge()

    def render(self):
        text = " ".join(self.items)
        if not self.show_numbers:
            text = re.sub('.', '-', text)

        return Align.center(Text(text), vertical="middle")

class NumFooter(Widget):
    def render(self) -> RenderableType:
        style = "white on rgb(0,100,20)"
        return Text(text=" Q quit, N new challenge", style=style, justify="left")

class NumSeqView(GridView):
    app_state: AppState
    app_settings: AppSettings
    show_numbers: ShowNumbers
    input_numbers: InputNumbers
    current_level: int

    def incr_level(self):
        d = load_settings()
        d['seq_length'] = self.current_level + 1
        add_settings(CHALLENGE_ID, json.dumps(d))

    def decr_level(self):
        if self.current_level <= 2:
            return
        d = load_settings()
        d['seq_length'] = self.current_level - 1
        add_settings(CHALLENGE_ID, json.dumps(d))

    def on_key(self, event: events.Key) -> None:
        if event.key == "n":
            s = load_settings()
            self.current_level = s["seq_length"]
            self.show_numbers.new_challenge()

            self.input_numbers.content = ""
            self.app_state = AppState.SHOW_NUMBERS
            self.show_numbers.show_numbers = True
            self.input_numbers.input_state = self.app_state
            return

        if self.app_state in [AppState.SHOW_NUMBERS, AppState.WRONG]:
            self.app_state = AppState.STARTED_ANSWER

        if self.app_state in [AppState.STARTED_ANSWER, AppState.WRONG]:
            self.show_numbers.show_numbers = False

            if event.key == "enter":
                answer = " ".join(self.show_numbers.items)
                self.app_state = self.input_numbers.check_answer(answer)

        if self.app_state == AppState.WRONG:
            self.decr_level()

        if self.app_state == AppState.CORRECT:
            self.incr_level()
            self.show_numbers.show_numbers = True

        self.input_numbers.input_state = self.app_state

    async def on_mount(self) -> None:
        self.app_state = AppState.SHOW_NUMBERS
        s = load_settings()
        self.current_level = s["seq_length"]

        self.footer = NumFooter()

        self.show_numbers = ShowNumbers()
        self.input_numbers = InputNumbers()

        await self.input_numbers.focus()

        self.grid.set_align("center", "center")
        self.grid.set_gap(1, 1)
        self.grid.add_column("column", repeat=1)
        self.grid.add_row("row", repeat=2)
        self.grid.add_row("row", repeat=1, size=1)

        self.grid.add_widget(self.show_numbers)
        self.grid.add_widget(self.input_numbers)
        self.grid.add_widget(self.footer)
