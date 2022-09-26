#!/usr/bin/env python3

import json
from typing import Optional, TypedDict

from textual.app import App
from textual.widgets import Button, ButtonPressed
from textual.views._grid_view import GridView

import mmm.db as db
from mmm import IS_DEV
from mmm.components.home import HomeView

from mmm.components.challenge_interface import ChallengeInterface
from mmm.components.static_number_sequence import StaticNumSeqView
from mmm.components.timed_number_sequence import TimedNumSeqView
from mmm.components.math_arithmetic import MathArithmeticView

from mmm.components.home import VIEW_ID as HomeId
from mmm.components.static_number_sequence import VIEW_ID as StaticNumId
from mmm.components.timed_number_sequence import VIEW_ID as TimedNumId
from mmm.components.math_arithmetic import VIEW_ID as MathArithId

VIEW_ID = "Memory Master Mind"

class Settings(TypedDict):
    last_challenge: str

def default_settings() -> Settings:
    return Settings(
        # Load Home view for the first time.
        last_challenge = HomeId,
    )

def load_settings() -> Settings:
    res = db.get_settings(VIEW_ID)
    if res:
        d: Settings = json.loads(res[2])
        return d
    else:
        d = default_settings()
        s = json.dumps(d)
        db.save_settings(VIEW_ID, s)
        return d

class MmmApp(App):
    home: HomeView
    current_challenge: Optional[ChallengeInterface]

    async def on_load(self):
        await self.bind("h", "home", "Home")
        await self.bind("q", "quit", "Quit")
        await self.bind("p", "preferences", "Preferences")

    async def dock_view(self, view: GridView):
        self.view.layout.docks.clear() # type: ignore
        self.view.widgets.clear()
        await self.view.dock(view, edge="top")

    async def action_home(self):
        self.current_challenge = None
        await self.dock_view(self.home)
        await self.home.header.focus()

    async def action_preferences(self):
        if self.current_challenge is None:
            return

        await self.dock_view(self.current_challenge.get_preferences_view())

    async def load_view(self, name):
        if name in ["submit_pref", "cancel_pref"]:
            if self.current_challenge is not None:
                await self.dock_view(self.current_challenge)
                self.current_challenge.new_challenge()
                await self.current_challenge.focus_input()
            return

        if name in [StaticNumId, TimedNumId, MathArithId]:
            d = load_settings()
            d["last_challenge"] = name
            db.save_settings(VIEW_ID, json.dumps(d))

        if name == HomeId:
            await self.action_home()

        elif name == StaticNumId:
            self.current_challenge = StaticNumSeqView()
            await self.dock_view(self.current_challenge)

        elif name == TimedNumId:
            self.current_challenge = TimedNumSeqView()
            await self.dock_view(self.current_challenge)

        elif name == MathArithId:
            self.current_challenge = MathArithmeticView()
            await self.dock_view(self.current_challenge)

    async def handle_button_pressed(self, message: ButtonPressed) -> None:
        if isinstance(message.sender, Button):
            await self.load_view(message.sender.name)

    async def on_mount(self) -> None:
        self.home = HomeView()

        d = load_settings()
        await self.load_view(d['last_challenge'])

def start():
    db.db_init()
    if IS_DEV:
        MmmApp.run(title="MMM", log="textual.log")
    else:
        MmmApp.run(title="MMM")
