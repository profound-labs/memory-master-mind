#!/usr/bin/env python3

# Timed Number Sequence

import re
import math
from random import randint
import json
from typing import List

from mmm.types import TimedNumId, load_settings
import mmm.db as db
from mmm.components.footer import Footer
from mmm.components.form_label import FormLabel
from mmm.components.input_answer import InputAnswer
from mmm.components.challenge_interface import ChallengeInterface, ShowChallengeInterface
from mmm.components.preferences_interface import PreferencesInterface
from mmm.components.input_text import InputText

class ShowNumbers(ShowChallengeInterface):
    def new_challenge(self, regenerate: bool = True):
        d = load_settings(self.view_id)
        a = []
        for _ in range(0, d['level']):
            range_from = int(math.pow(10, d['digits_min']- 1)) - 1
            range_to = int(math.pow(10, d['digits_max'])) - 1

            n = randint(range_from, range_to)
            if d['zero_padded']:
                a.append(str(n).rjust(d['digits_max'], '0'))
            else:
                a.append(str(n))
        self.items = a

        self.current_item = 0

    def format_challenge(self) -> str:
        text = self.items[self.current_item]
        if not self.show_numbers:
            text = re.sub('.', '-', text)

        return text

    def format_answers(self, _: bool) -> List[str]:
        a = " ".join(self.items)
        return [a]

    def generate_answer(self) -> str:
        return " ".join(self.items)


class PreferencesView(PreferencesInterface):
    def save_settings(self):
        d = load_settings(self.view_id)

        for k in ['digits_min', 'digits_max', 'level_max', 'ch_per_level', 'seconds_per_level']:
            d[k] = int(self.inputs[k].content)

        if self.inputs['zero_padded'].content == "True":
            d['zero_padded'] = True
        else:
            d['zero_padded'] = False

        db.save_settings(self.view_id, json.dumps(d))

    def setup_labels_inputs(self):
        d = load_settings(self.view_id)

        self.labels['digits_min'] = FormLabel(label="Digits min:")
        self.labels['digits_max'] = FormLabel(label="Digits max:")
        self.labels['level_max'] = FormLabel(label="Level max:")
        self.labels['ch_per_level'] = FormLabel(label="Challenges per level:")
        self.labels['seconds_per_level'] = FormLabel(label="Seconds per level:")
        self.labels['zero_padded'] = FormLabel(label="Zero padded:")

        for k in ['digits_min', 'digits_max', 'level_max', 'ch_per_level', 'seconds_per_level']:
            self.inputs[k] = InputText(
                label=k,
                content=str(d[k]),
                allow_regex=r'[0-9]',
                input_height=1,
            )

        self.inputs['zero_padded'] = InputText(
            label='zero_padded',
            content=str(d['zero_padded']),
            is_bool=True,
            input_height=1,
        )

        for idx, k in enumerate(self.inputs.keys()):
            self.grid.add_row(f"r{idx+2}", size=1)
            self.grid.add_widget(self.labels[k])
            self.grid.add_widget(self.inputs[k])


class TimedNumSeqView(ChallengeInterface):
    def init_attr(self):
        self.view_id = TimedNumId
        self.help_md_filename = "timed_number_sequence.md"

    def init_components(self):
        self.preferences_view = PreferencesView(self.view_id)

        self.footer = Footer()
        self.footer.level = self.current_level

        self.show_numbers = ShowNumbers(self.view_id)
        self.input_answer = InputAnswer(self.get_instruction())

        self.show_challenge_blocks_keys = True
        self.input_answer.show_challenge_blocks_keys = True

    def get_instruction(self) -> str:
        return "The numbers will appear one by one. Memorize, then type them."

    def get_preferences_view(self):
        self.preferences_view = PreferencesView(self.view_id)
        return self.preferences_view

    def blink_number(self):
        self.show_numbers.items.append("")
        current = len(self.show_numbers.items) - 1
        old_current_item = self.show_numbers.current_item
        self.show_numbers.current_item = current
        def reveal():
            self.show_numbers.current_item = old_current_item
            self.show_numbers.items.pop()
        self.set_timer(0.5, reveal)

    def show_next_per_secs(self):
        d = load_settings(self.view_id)
        secs = d['seconds_per_level']

        if (self.challenge_timer.seconds_remain - 1) % secs == 0:
            self.show_numbers.show_next_item()
            self.blink_number()

    def start_timer(self, seconds_per_level: int):
        self.challenge_timer.stop_timer()
        if seconds_per_level != 0:
            secs = seconds_per_level * self.current_level
            self.challenge_timer.start_timer(
                secs=secs,
                final_cb=self.do_started_answer,
                tick_cb=self.show_next_per_secs,
            )
