#!/usr/bin/env python3

from textual.app import App
from .db import db_init
from .components.number_sequence import NumSeqView

class MmmApp(App):
    async def on_load(self):
        await self.bind("q", "quit", "Quit")

    async def on_mount(self) -> None:
        await self.view.dock(NumSeqView(), edge="top")

def start():
    db_init()
    MmmApp.run(title="MMM", log="textual.log")
