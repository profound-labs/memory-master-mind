#!/usr/bin/env python3

from typing import Optional

from rich.console import RenderableType

from textual import events
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import Button, ButtonPressed

class FormButton(Widget):
    is_selected = Reactive(False)
    label: str = ""
    name: str = ""
    button: Button

    def __init__(self, label: str, name: Optional[str] = None):
        super().__init__()
        self.label = label
        if name:
            self.name = name
        else:
            self.name = label

    def on_enter(self) -> None:
        self.is_selected = True

    def on_leave(self) -> None:
        self.is_selected = False

    async def on_click(self, _: events.Click) -> None:
        await self.emit(ButtonPressed(self.button))

    def render(self) -> RenderableType:
        if self.is_selected:
            style = "bold black on yellow"
        else:
            style = "white on rgb(50,57,50)"

        self.button = Button(
            label=self.label,
            name=self.name,
            style=style,
        )
        return self.button
