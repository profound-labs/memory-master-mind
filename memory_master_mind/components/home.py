#!/usr/bin/env python3

import json

from typing import List, Optional

from textual import events
from textual.widgets import ButtonPressed
from textual.views._grid_view import GridView
from memory_master_mind.components.footer import Footer
from memory_master_mind.components.form_label import FormLabel
from memory_master_mind.components.input_text import InputText
from memory_master_mind.components.preferences_interface import PreferencesInterface

import memory_master_mind.db as db
from memory_master_mind.types import app_load_settings
from memory_master_mind.types import AppId, HomeId, StaticNumId, TimedNumId, MathArithId, QuotesId
from memory_master_mind.components.header import Header
from memory_master_mind.components.form_button import FormButton


class PreferencesView(PreferencesInterface):
    def save_settings(self):
        d = app_load_settings()

        d['stats_path'] = self.inputs['stats_path'].content

        if self.inputs['save_stats'].content == "True":
            d['save_stats'] = True
        else:
            d['save_stats'] = False

        if self.inputs['stats_include_settings'].content == "True":
            d['stats_include_settings'] = True
        else:
            d['stats_include_settings'] = False

        db.save_settings(AppId, json.dumps(d))

    def setup_labels_inputs(self):
        d = app_load_settings()

        self.labels['save_stats'] = FormLabel(label="Save stats:")
        self.labels['stats_include_settings'] = FormLabel(label="Stats include settings:")
        self.labels['stats_path'] = FormLabel(label="Stats CSV file path:")

        self.inputs['save_stats'] = InputText(
            label='save_stats',
            content=str(d['save_stats']),
            is_bool=True,
            input_height=1,
        )

        self.inputs['stats_include_settings'] = InputText(
            label='stats_include_settings',
            content=str(d['stats_include_settings']),
            is_bool=True,
            input_height=1,
        )

        self.inputs['stats_path'] = InputText(
            label='stats_path',
            content=str(d['stats_path']),
            is_text=True,
            input_height=1,
        )

        for idx, k in enumerate(self.inputs.keys()):
            self.grid.add_row(f"r{idx+2}", size=1)
            self.grid.add_widget(self.labels[k])
            self.grid.add_widget(self.inputs[k])

class HomeView(GridView):
    view_id: str
    preferences_view: PreferencesInterface
    challenges: List[FormButton] = []
    selected_idx: Optional[int] = None

    def __init__(self):
        super().__init__()
        self.view_id = HomeId
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

        self.grid.add_row("spc1")
        self.grid.add_widget(Header(title=""))

        self.grid.add_row("row1", size=1)
        self.grid.add_widget(self.header)

        await self.header.focus()

        for i in labels:
            self.challenges.append(
                FormButton(label=i)
            )

        self.challenges.append(FormButton(label="Help"))

        for idx, _ in enumerate(self.challenges):
            self.grid.add_row(f"row{idx+2}", size=1)
            self.grid.add_widget(self.challenges[idx])

        self.footer = Footer()
        self.footer.new_challenge = False
        self.footer.show_answer = False
        self.footer.show_level = False
        self.footer.select_input = True

        self.grid.add_row("spc2")
        self.grid.add_widget(Header(title=""))

        self.grid.add_row("footer", size=1)
        self.grid.add_widget(self.footer)

    def get_preferences_view(self):
        self.preferences_view = PreferencesView(AppId)
        return self.preferences_view
