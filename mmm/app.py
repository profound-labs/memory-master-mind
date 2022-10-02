#!/usr/bin/env python3

import json
from typing import Optional, TypedDict
from rich.markdown import Markdown

from textual.app import App
from textual.widgets import Button, ButtonPressed, ScrollView
from textual.views._grid_view import GridView
from mmm.components.footer import Footer

import mmm.db as db
from mmm import IS_DEV, MARKDOWN_DIR
from mmm.components.home import HomeView

from mmm.components.challenge_interface import ChallengeInterface
from mmm.components.static_number_sequence import StaticNumSeqView
from mmm.components.timed_number_sequence import TimedNumSeqView
from mmm.components.math_arithmetic import MathArithmeticView
from mmm.components.quotes import QuotesView

from mmm.types import AppId, HomeId, StaticNumId, TimedNumId, MathArithId, QuotesId

class Settings(TypedDict):
    last_challenge: str

def default_settings() -> Settings:
    return Settings(
        # Load Home view for the first time.
        last_challenge = HomeId,
    )

def load_settings() -> Settings:
    res = db.get_settings(AppId)
    if res:
        d: Settings = json.loads(res[2])
        return d
    else:
        d = default_settings()
        s = json.dumps(d)
        db.save_settings(AppId, s)
        return d

class MmmApp(App):
    home: HomeView
    current_challenge: Optional[ChallengeInterface]
    menu_enabled: bool = True

    async def on_load(self):
        await self.bind("h", "home", "Home")
        await self.bind("q", "maybe_quit", "Quit")
        await self.bind("p", "preferences", "Preferences")
        await self.bind("escape", "go_back", "Go Back")
        await self.bind("?", "help", "Help")

    def toggle_menu(self):
        self.menu_enabled = not self.menu_enabled

    async def dock_view(self, view: GridView):
        self.view.layout.docks.clear() # type: ignore
        self.view.widgets.clear()
        await self.view.dock(view, edge="top")

    async def action_maybe_quit(self):
        if not self.menu_enabled:
            return
        await self.action_quit()

    async def action_home(self):
        if not self.menu_enabled:
            return
        self.current_challenge = None
        await self.dock_view(self.home)
        await self.home.header.focus()

    async def action_preferences(self):
        if not self.menu_enabled:
            return
        if self.current_challenge is None:
            return

        await self.dock_view(self.current_challenge.get_preferences_view())

    async def action_go_back(self):
        if not self.menu_enabled:
            return
        if self.current_challenge is None:
            return

        await self.load_view(self.current_challenge.view_id)

    async def action_help(self):
        if not self.menu_enabled:
            return
        if self.current_challenge is None:
            return

        self.view.layout.docks.clear() # type: ignore
        self.view.widgets.clear()

        footer = Footer()
        footer.scroll = True
        footer.go_back = True
        footer.new_challenge = False
        footer.preferences = False
        footer.show_answer = False
        footer.show_help = False
        footer.show_level = False

        help_view = ScrollView(gutter=1)

        await self.view.dock(help_view, edge="top")
        await self.view.dock(footer, edge="bottom", size=1, z=99)

        md_path = MARKDOWN_DIR.joinpath(self.current_challenge.help_md_filename)

        async def get_markdown() -> None:
            with open(md_path, "r", encoding="utf8") as f:
                md = Markdown(f.read(), hyperlinks=True)
            await help_view.update(md)

        await help_view.focus()

        await self.call_later(get_markdown)

    async def load_view(self, name):
        if name in ["submit_pref", "cancel_pref"]:
            if self.current_challenge is not None:
                await self.dock_view(self.current_challenge)
                self.current_challenge.new_challenge()
                await self.current_challenge.focus_input()
            return

        if name in [StaticNumId, TimedNumId, MathArithId, QuotesId]:
            d = load_settings()
            d["last_challenge"] = name
            db.save_settings(AppId, json.dumps(d))

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

        elif name == QuotesId:
            self.current_challenge = QuotesView()
            self.current_challenge.is_text_challenge = True
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
