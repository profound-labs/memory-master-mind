#!/usr/bin/env python3

from typing import Optional

from rich.console import RenderableType

from textual.widget import Widget
from textual.widgets import Button

class FormLabel(Widget):
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

    def render(self) -> RenderableType:
        self.button = Button(
            label=self.label,
            name=self.name,
            style="white on rgb(0,0,100)",
        )
        return self.button
