#!/usr/bin/env python3

# Static Number Sequence

import re
import math
from random import randint
import json

from mmm.types import StaticNumId, load_settings
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

    def format_challenge(self) -> str:
        text = " ".join(self.items)
        if not self.show_numbers:
            text = re.sub('.', '-', text)

        return text

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
