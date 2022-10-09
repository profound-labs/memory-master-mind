#!/usr/bin/env python3

from typing import Dict, Optional

from textual import events
from textual.views._grid_view import GridView
from textual.widgets import ButtonPressed

from memory_master_mind.components.header import Header
from memory_master_mind.components.footer import Footer
from memory_master_mind.components.input_text import InputText
from memory_master_mind.components.form_button import FormButton
from memory_master_mind.components.form_label import FormLabel


class PreferencesInterface(GridView):
    view_id: str
    labels: Dict[str, FormLabel]
    inputs: Dict[str, InputText]
    submit_btn: FormButton
    cancel_btn: FormButton
    selected_idx: Optional[int] = None

    def __init__(self, view_id: str):
        super().__init__()
        self.view_id = view_id
        self.labels = dict()
        self.inputs = dict()

    def save_settings(self):
        raise NotImplementedError

    def set_menu_enabled(self, x: bool):
        self.app.menu_enabled = x # type: ignore
        self.footer.menu_enabled = x

    async def highlight_selected(self):
        if self.selected_idx is None:
            return

        selected_key = ""
        for idx, k in enumerate(self.inputs.keys()):
            await self.inputs[k].set_selected(idx == self.selected_idx)
            if idx == self.selected_idx:
                selected_key = k

        if selected_key != "" and self.inputs[selected_key].is_text:
            self.set_menu_enabled(False)
        else:
            self.set_menu_enabled(True)

    async def select_next(self):
        if self.selected_idx is None:
            self.selected_idx = 0
        elif self.selected_idx == len(self.inputs) - 1:
            self.selected_idx = 0
        else:
            self.selected_idx += 1

        await self.highlight_selected()

    async def select_prev(self):
        if self.selected_idx is None:
            self.selected_idx = len(self.inputs) - 1
        elif self.selected_idx == 0:
            self.selected_idx = len(self.inputs) - 1
        else:
            self.selected_idx -= 1

        await self.highlight_selected()

    async def submit(self):
        self.save_settings()
        await self.emit(ButtonPressed(self.submit_btn.button))

    async def cancel(self):
        await self.emit(ButtonPressed(self.cancel_btn.button))

    async def on_key(self, event: events.Key) -> None:
        if event.key == "down" or event.key == "ctrl+i" or event.key == "j":
            # ctrl+i is Tab
            await self.select_next()

        if event.key == "up" or event.key == "shift+tab" or event.key == "k":
            await self.select_prev()

        if event.key == "enter":
            await self.submit()

        if event.key == "escape":
            await self.cancel()

    def setup_labels_inputs(self):
        raise NotImplementedError

    async def on_mount(self):
        self.submit_btn = FormButton(label="OK [Enter]", name="submit_pref")
        self.cancel_btn = FormButton(label="Cancel [Esc]", name="cancel_pref")

        self.grid.set_align("center", "center")
        self.grid.set_gap(1, 0)
        self.grid.add_column("c1")
        self.grid.add_column("c2")

        self.grid.add_row("spc0", size=1)
        self.grid.add_areas(spc0="c1-start|c2-end,spc0")
        self.grid.add_widget(Header(title=""), area="spc0")

        self.header = Header(title="Preferences: " + self.view_id)

        self.grid.add_row("r1", size=2)
        self.grid.add_areas(area1="c1-start|c2-end,r1")
        self.grid.add_widget(widget=self.header, area="area1")

        await self.header.focus()

        self.setup_labels_inputs()

        self.grid.add_row("spc1", size=1)
        self.grid.add_row("btn", size=1)

        self.grid.add_areas(area2="c1,btn")
        self.grid.add_areas(area3="c2,btn")

        self.grid.add_widget(self.submit_btn, area="area2")
        self.grid.add_widget(self.cancel_btn, area="area3")

        self.grid.add_row("spc2")

        self.grid.add_row("footer", size=1)
        self.grid.add_areas(footer="c1-start|c2-end,footer")

        self.footer = Footer()
        self.footer.select_input = True
        self.footer.preferences = False
        self.footer.show_answer = False
        self.footer.show_help = False
        self.footer.new_challenge = False
        self.footer.show_level = False

        self.grid.add_widget(self.footer, area="footer")
