#!/usr/bin/env python3

import json
import datetime
from pathlib import Path
from typing import Optional
from rich.markdown import Markdown

from textual.app import App
from textual.widgets import Button, ButtonPressed, ScrollView
from textual.views._grid_view import GridView
from memory_master_mind.components.footer import Footer

import memory_master_mind.db as db
from memory_master_mind import IS_DEV, MARKDOWN_DIR
from memory_master_mind.components.home import HomeView

from memory_master_mind.components.challenge_interface import ChallengeInterface
from memory_master_mind.components.static_number_sequence import StaticNumSeqView
from memory_master_mind.components.timed_number_sequence import TimedNumSeqView
from memory_master_mind.components.math_arithmetic import MathArithmeticView
from memory_master_mind.components.quotes import QuotesView

from memory_master_mind.types import AppId, HomeId, StaticNumId, Stats, TimedNumId, MathArithId, QuotesId
from memory_master_mind.types import app_load_settings, load_settings

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
            await self.dock_view(self.home.get_preferences_view())
        else:
            await self.dock_view(self.current_challenge.get_preferences_view())

    async def action_go_back(self):
        if not self.menu_enabled:
            return

        if self.current_challenge is None:
            await self.action_home()
        else:
            await self.load_view(self.current_challenge.view_id)

    async def action_help(self, help_md_filename: Optional[str] = None):
        if not self.menu_enabled:
            return
        if self.current_challenge is None and help_md_filename is None:
            help_md_filename = "mmm_help.md"

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

        if help_md_filename is not None:
            md_path = MARKDOWN_DIR.joinpath(help_md_filename)
        elif self.current_challenge is not None:
            md_path = MARKDOWN_DIR.joinpath(self.current_challenge.help_md_filename)
        else:
            return

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
                self.current_challenge.new_challenge(regenerate=False)
                await self.current_challenge.focus_input()
            else:
                await self.action_home()

        if name == "Help":
            await self.action_help("mmm_help.md")

        if name in [StaticNumId, TimedNumId, MathArithId, QuotesId]:
            d = app_load_settings()
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

        d = app_load_settings()
        await self.load_view(d['last_challenge'])

    def save_stats(self):
        d = app_load_settings()
        if not d['save_stats'] or d['stats_path'] == "":
            return

        stats_path = Path(d['stats_path']).expanduser()

        if self.current_challenge is None:
            return

        secs = f"{self.current_challenge.input_answer.time_elapsed:.1f}"

        if d['stats_include_settings']:
            s = load_settings(self.current_challenge.view_id)
            a = list(map(lambda i: f"{i[0]}={i[1]}", s.items()))
            setts = '"' + "|".join(a) + '"'
        else:
            setts = ''

        stats = Stats(
            datetime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            challenge_name=self.current_challenge.view_id,
            level=str(self.current_challenge.current_level),
            solved_in_secs=secs,
            first_try=str(self.current_challenge.first_try),
            settings=setts,
        )

        keys = stats.keys()
        csv_header = ",".join(keys)

        values = []
        for k in keys:
            values.append(stats[k])

        csv_row = ",".join(values)

        if not stats_path.exists():
            with open(stats_path, "w", encoding="utf8") as f:
                f.write(csv_header + "\n")

        with open(stats_path, "a", encoding="utf8") as f:
            f.write(csv_row + "\n")

def start():
    db.db_init()
    if IS_DEV:
        MmmApp.run(title="MMM", log="textual.log")
    else:
        MmmApp.run(title="MMM")
