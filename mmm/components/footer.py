#!/usr/bin/env python3

from rich.console import RenderableType
from rich.text import Text

from textual.reactive import Reactive
from textual.widget import Widget

class Footer(Widget):
    new_challenge = Reactive(True)
    show_answer = Reactive(False)
    level = Reactive(1)

    def render(self) -> RenderableType:
        style = "white on rgb(0,100,20)"
        labels = ["H home", "Q quit", "P preferences"]
        if self.new_challenge:
            labels.append("N new challenge")
        if self.show_answer:
            labels.append("S show answer")
        labels.append(f"Level {self.level}")
        text = " " + ", ".join(labels)
        return Text(text=text, style=style, justify="left")
