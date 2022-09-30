#!/usr/bin/env python3

import re
from typing import Optional

from rich.align import Align
from rich.box import ROUNDED
from rich.console import RenderableType
from rich.panel import Panel
from rich.text import Text

from textual import events
from textual.reactive import Reactive
from textual.widget import Widget

class InputText(Widget):
    label = Reactive("")
    content = Reactive("")
    is_selected = Reactive(False)
    is_bool = False
    is_text = False
    allow_regex: Optional[str] = None
    input_height: int

    def __init__(self,
                 label: str,
                 content: str = "",
                 is_bool: bool = False,
                 is_text: bool = False,
                 allow_regex: Optional[str] = None,
                 input_height: int = 3):
        super().__init__()
        self.label = label
        self.content = content
        self.is_bool = is_bool
        self.is_text = is_text
        self.allow_regex = allow_regex
        self.input_height = input_height

    async def set_selected(self, x: bool):
        self.is_selected = x
        if x:
            await self.focus()

    async def on_enter(self) -> None:
        await self.set_selected(True)

    async def on_leave(self) -> None:
        await self.set_selected(False)

    def on_key(self, event: events.Key) -> None:
        if not self.is_selected:
            return

        if event.key in ["ctrl+i", "shift+tab", "enter", "up", "down", "j", "k"]:
            return

        if self.is_bool:
            if self.content == "True":
                self.content = "False"
            else:
                self.content = "True"
            return

        if event.key == "ctrl+h":
            self.content = self.content[:-1]
            return

        if self.allow_regex:
            if re.search(self.allow_regex, event.key):
                self.content += event.key
        else:
            self.content += event.key

    def render(self) -> RenderableType:

        if self.is_selected:
            text = "> " + self.content
            border_style = "white"
            style = "white on rgb(0,57,0)"
        else:
            text = "  " + self.content
            border_style = "green"
            style = "white on rgb(50,57,50)"

        renderable = Align.left(
            renderable=Text(text=text),
            style=style,
        )

        if self.input_height < 3:
            return renderable
        else:
            return Panel(
                renderable,
                title=None,
                title_align="center",
                height=self.input_height,
                style=style,
                border_style=border_style,
                box=ROUNDED,
                padding=(0,0),
            )
