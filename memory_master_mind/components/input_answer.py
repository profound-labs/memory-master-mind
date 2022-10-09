#!/usr/bin/env python3

import re
import time
from typing import List

from rich.align import Align
from rich.console import RenderableType
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from textual import events
from textual.reactive import Reactive
from textual.widget import Widget

from memory_master_mind.types import RE_PUNCT, State

class InputAnswer(Widget):
    content = Reactive("")
    state = Reactive(State.SHOW_CHALLENGE)
    instruction: str
    only_numbers: bool = True
    time_challenge_started: float = 0.0
    time_elapsed: float = 0.0
    show_challenge_blocks_keys: bool = False

    def __init__(self, instruction: str):
        super().__init__()
        self.instruction = instruction

    def new_challenge(self):
        self.content = ""
        self.time_challenge_started = time.time()

    def end_challenge(self):
        t = time.time()
        self.time_elapsed = t - self.time_challenge_started

    def on_key(self, event: events.Key) -> None:
        if self.state == State.CORRECT:
            return

        if self.only_numbers:
            if event.key in ["h", "q", "p", "s", "?", "enter", "escape"]:
                return
        else:
            if self.app.menu_enabled == True: # type: ignore
                if event.key in ["h", "q", "p", "s", "?", "enter", "escape", "ctrl+i"]:
                    return
            elif event.key in ["escape", "ctrl+i"]:
                return

        if self.state is State.SHOW_CHALLENGE and self.show_challenge_blocks_keys:
            return

        if event.key == "ctrl+h":
            # ctrl+h is Backspace
            self.content = self.content[:-1]
        elif self.only_numbers:
            if re.search(r'[0-9\. -]', event.key):
                    self.content += event.key
        else:
            if event.key == "enter":
                self.content += "\n"
            else:
                self.content += event.key

    def check_answer(self, correct_answer: str) -> State:
        text = self.content.strip().lower()
        text = re.sub(RE_PUNCT, '', text)
        text = re.sub(r'  +', ' ', text)

        answer = correct_answer.strip().lower()
        answer = re.sub(RE_PUNCT, '', answer)
        answer = re.sub(r'  +', ' ', answer)

        if text == answer:
            self.state = State.CORRECT
        else:
            self.state = State.WRONG

        return self.state

    def render(self) -> RenderableType:
        s = self.content + "_"
        renderable = Align.left(Text(s, style="bold"))

        title = self.instruction

        if self.state == State.STARTED_ANSWER:
            style = "bold white on rgb(50,57,50)"
            border_style = Style(color="yellow")

        elif self.state == State.CORRECT:
            title = f"Correct! Solved in {self.time_elapsed:.1f}s"
            style = "bold white on rgb(50,57,50)"
            border_style = Style(color="green")

        elif self.state == State.WRONG:
            style = "bold white on rgb(50,57,50)"
            border_style = Style(color="red")

        elif self.state == State.SHOW_ANSWER:
            title = "Press any key for a new challenge"
            style = "white on rgb(50,57,50)"
            border_style = Style(color="white")

        else:
            # State.SHOW_CHALLENGE
            style = "white on rgb(50,57,50)"
            border_style = Style(color="white")

        return Panel(
            renderable,
            title=title,
            title_align="center",
            style=style,
            border_style=border_style,
        )
