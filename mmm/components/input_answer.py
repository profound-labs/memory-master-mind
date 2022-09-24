#!/usr/bin/env python3

import re

from rich.align import Align
from rich.console import RenderableType
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from textual import events
from textual.reactive import Reactive
from textual.widget import Widget

from mmm.types import State

class InputAnswer(Widget):
    content = Reactive("")
    state = Reactive(State.SHOW_CHALLENGE)
    instruction: str

    def __init__(self, instruction: str):
        super().__init__()
        self.instruction = instruction

    def on_key(self, event: events.Key) -> None:
        if self.state == State.CORRECT:
            return

        if event.key in ["h", "q", "p"]:
            return

        if event.key == "ctrl+h":
            # ctrl+h is Backspace
            self.content = self.content[:-1]
        elif re.search(r'[0-9\. -]', event.key):
                self.content += event.key

    def check_answer(self, correct_answer: str) -> State:
        if self.content.strip() == correct_answer:
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
            title = "Correct!"
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
