#!/usr/bin/env python3

from typing import Optional

from textual.widget import Widget
from rich.text import Text

class Header(Widget):
    title: str
    title_style: str

    def __init__(self, title: str, style = Optional[str]):
        super().__init__()

        self.title = title
        if style is None:
            self.title_style = "white on black"
        else:
            self.title_style = str(style)

    def render(self):
        return Text(text=self.title,
                    style=self.title_style,
                    justify="center")
