#!/usr/bin/env python3

from typing import List
from rich.align import Align
from rich.text import Text

from textual.reactive import Reactive
from textual.widget import Widget

from mmm.types import State

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

    def format_challenge(self) -> str:
        raise NotImplementedError

    def generate_answer(self) -> str:
        raise NotImplementedError

    def format_answers(self, for_display: bool) -> List[str]:
        text = self.format_challenge()
        answer = self.generate_answer()
        if text == answer:
            return [answer]

        if for_display:
            a = text + "\n= " + answer
            return [a]
        else:
            return [answer]

    def show_next_item(self):
        if self.current_item < len(self.items) - 1:
            self.current_item += 1

    # def on_mount(self):
    #     # NOTE: Not needed: self.new_challenge()
    #     # challenge.new_challenge() will call show_challenge.new_challenge()

    def render(self):
        if self.state in [State.SHOW_ANSWER, State.CORRECT]:
            text = self.format_answers(True)[0]
        else:
            text = self.format_challenge()
        return Align.center(Text(text), vertical="middle")
