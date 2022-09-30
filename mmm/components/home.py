#!/usr/bin/env python3

from typing import List, Optional

from textual import events
from textual.widgets import ButtonPressed
from textual.views._grid_view import GridView

from mmm.types import StaticNumId, TimedNumId, MathArithId, QuotesId
from mmm.components.header import Header
from mmm.components.form_button import FormButton

class HomeView(GridView):
    challenges: List[FormButton] = []
    selected_idx: Optional[int] = None

    def __init__(self):
        super().__init__()
        self.header = Header(title="Memory Master Mind")

    def highlight_selected(self):
        if self.selected_idx is not None:
            for idx, _ in enumerate(self.challenges):
                if idx == self.selected_idx:
                    self.challenges[idx].is_selected = True
                else:
                    self.challenges[idx].is_selected = False

    def select_next(self):
        if self.selected_idx is None:
            self.selected_idx = 0
        elif self.selected_idx == len(self.challenges) - 1:
            self.selected_idx = 0
        else:
            self.selected_idx += 1

        self.highlight_selected()

    def select_prev(self):
        if self.selected_idx is None:
            self.selected_idx = len(self.challenges) - 1
        elif self.selected_idx == 0:
            self.selected_idx = len(self.challenges) - 1
        else:
            self.selected_idx -= 1

        self.highlight_selected()

    async def click_selected(self):
        if self.selected_idx is None:
            return
        event = ButtonPressed(self.challenges[self.selected_idx].button)
        await self.emit(event)

    async def on_key(self, event: events.Key) -> None:
        if event.key == "down" or event.key == "ctrl+i" or event.key == "j":
            # ctrl+i is Tab
            self.select_next()

        if event.key == "up" or event.key == "shift+tab" or event.key == "k":
            self.select_prev()

        if event.key == "enter":
            await self.click_selected()

    async def on_mount(self) -> None:
        labels = [
            StaticNumId,
            TimedNumId,
            MathArithId,
            QuotesId,
        ]

        self.grid.set_align("center", "center")
        self.grid.set_gap(0, 1)
        self.grid.add_column("column")

        self.grid.add_row("row1", size=1)
        self.grid.add_widget(self.header)

        await self.header.focus()

        for i in labels:
            self.challenges.append(
                FormButton(label=i)
            )

        for idx, _ in enumerate(self.challenges):
            self.grid.add_row(f"row{idx+2}", size=1)
            self.grid.add_widget(self.challenges[idx])
