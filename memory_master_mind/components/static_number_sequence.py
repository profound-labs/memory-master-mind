#!/usr/bin/env python3

# Static Number Sequence

import re
import math
from random import randint
import json
from typing import List

from rich.text import Text

from memory_master_mind.types import StaticNumId, load_settings, is_prime
import memory_master_mind.db as db
from memory_master_mind.components.footer import Footer
from memory_master_mind.components.form_label import FormLabel
from memory_master_mind.components.input_answer import InputAnswer
from memory_master_mind.components.challenge_interface import ChallengeInterface, ShowChallengeInterface
from memory_master_mind.components.preferences_interface import PreferencesInterface
from memory_master_mind.components.input_text import InputText

class ShowNumbers(ShowChallengeInterface):
    def new_challenge(self, regenerate: bool = True):
        d = load_settings(self.view_id)
        a: List[str] = []
        for _ in range(0, d['level']):
            range_from = int(math.pow(10, d['digits_min']- 1)) - 1
            range_to = int(math.pow(10, d['digits_max'])) - 1

            n = randint(range_from, range_to)
            if d['zero_padded']:
                a.append(str(n).rjust(d['digits_max'], '0'))
            else:
                a.append(str(n))
        self.items = a

    def format_challenge_plain(self) -> str:
        text = " ".join(self.items)
        if not self.show_numbers:
            text = re.sub('.', '-', text)

        return text

    def format_challenge_rich(self) -> Text:
        if self.show_numbers:
            d = load_settings(self.view_id)
            text = Text()
            for idx, i in enumerate(self.items):
                if idx != 0:
                    text.append(" ")

                if i.isdigit() and d['primes_are_red'] and is_prime(int(i)):
                    text.append(i, style="red")
                else:
                    text.append(i)

        else:
            s = " ".join(self.items)
            s = re.sub('.', '-', s)
            text = Text(s)

        return text

    def generate_answer(self) -> str:
        return " ".join(self.items)


class PreferencesView(PreferencesInterface):
    def save_settings(self):
        d = load_settings(self.view_id)

        for k in ['digits_min', 'digits_max', 'level_max', 'ch_per_level', 'seconds_per_level']:
            d[k] = int(self.inputs[k].content)

        if self.inputs['primes_are_red'].content == "True":
            d['primes_are_red'] = True
        else:
            d['primes_are_red'] = False

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
        self.labels['primes_are_red'] = FormLabel(label="Primes are red:")
        self.labels['zero_padded'] = FormLabel(label="Zero padded:")

        for k in ['digits_min', 'digits_max', 'level_max', 'ch_per_level', 'seconds_per_level']:
            self.inputs[k] = InputText(
                label=k,
                content=str(d[k]),
                allow_regex=r'[0-9]',
                input_height=1,
            )

        self.inputs['primes_are_red'] = InputText(
            label='primes_are_red',
            content=str(d['primes_are_red']),
            is_bool=True,
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


class StaticNumSeqView(ChallengeInterface):
    def init_attr(self):
        self.view_id = StaticNumId
        self.help_md_filename = "static_number_sequence.md"

    def init_components(self):
        self.preferences_view = PreferencesView(self.view_id)

        self.footer = Footer()
        self.footer.level = self.current_level

        self.show_numbers = ShowNumbers(self.view_id)
        self.input_answer = InputAnswer(self.get_instruction())

    def get_instruction(self) -> str:
        return "Memorize the numbers, then type them."

    def get_preferences_view(self):
        self.preferences_view = PreferencesView(self.view_id)
        return self.preferences_view
