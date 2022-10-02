#!/usr/bin/env python3

from rich.console import RenderableType
from rich.text import Text

from textual.reactive import Reactive
from textual.widget import Widget

class Footer(Widget):
    preferences = Reactive(True)
    new_challenge = Reactive(True)
    show_answer = Reactive(False)
    show_level = Reactive(True)
    show_help = Reactive(True)
    level = Reactive(1)
    menu_enabled = Reactive(True)
    scroll = Reactive(False)
    go_back = Reactive(False)

    def render(self) -> RenderableType:
        if self.menu_enabled:
            style = "white on rgb(0,100,20)"
            labels = ["H home", "Q quit"]
            if self.preferences:
                labels.append("P preferences")
            if self.new_challenge:
                labels.append("N new")
                labels.append("R repeat")
            if self.show_answer:
                labels.append("S show answer")
            if self.show_help:
                labels.append("? Help")
            if self.scroll:
                labels.append("Up/Down/PgUp/PgDown/Home/End scroll")
            if self.go_back:
                labels.append("Esc go back")

        else:
            style = "bold black on yellow"
            labels = ["[Text Input Mode] Press Tab to enable the menu"]

        if self.show_level:
            labels.append(f"Level {self.level}")
        text = " " + ", ".join(labels)
        return Text(text=text, style=style, justify="left")
