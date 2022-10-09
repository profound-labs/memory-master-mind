#!/usr/bin/env python3

from typing import List
from rich.align import Align
from rich.text import Text

from textual.reactive import Reactive
from textual.widget import Widget

from memory_master_mind.types import State

class ShowChallengeInterface(Widget):
    state = Reactive(State.SHOW_CHALLENGE)
    view_id: str
    items = Reactive([])
    show_numbers = Reactive(True)
    current_item = Reactive(0)

    def __init__(self, view_id: str):
        super().__init__()
        self.view_id = view_id

    def new_challenge(self, regenerate: bool = True):
        raise NotImplementedError

    def format_challenge_plain(self) -> str:
        raise NotImplementedError

    def format_challenge_rich(self) -> Text:
        raise NotImplementedError

    def generate_answer(self) -> str:
        raise NotImplementedError

    def format_answer_plain(self) -> str:
        return self.generate_answer()

    def format_answer_rich(self) -> Text:
        text = self.format_challenge_plain()
        answer = self.generate_answer()
        if text == answer:
            return self.format_challenge_rich()
        else:
            a = self.format_challenge_rich()
            a.append("\n= " + answer)
            return a

    def show_next_item(self):
        if self.current_item < len(self.items) - 1:
            self.current_item += 1

    # def on_mount(self):
    #     # NOTE: Not needed: self.new_challenge()
    #     # challenge.new_challenge() will call show_challenge.new_challenge()

    def render(self):
        if self.state in [State.SHOW_ANSWER, State.CORRECT]:
            text: Text = self.format_answer_rich()
        else:
            text: Text = self.format_challenge_rich()
        return Align.center(text, vertical="middle")
