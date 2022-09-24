#!/usr/bin/env python3

# Math (Arithmetic)

import re
import math
from random import randint
import json

import mmm.db as db
from mmm.components.footer import Footer
from mmm.components.form_label import FormLabel
from mmm.components.input_answer import InputAnswer
from mmm.components.challenge_interface import ChallengeInterface, ShowChallengeInterface, load_settings
from mmm.components.preferences_interface import PreferencesInterface
from mmm.components.input_text import InputText

VIEW_ID = "Math (Arithmetic)"

class ShowNumbers(ShowChallengeInterface):
    def new_challenge(self):
        d = load_settings(self.view_id)
        a = []
        for _ in range(0, d['level']):
            range_from = int(math.pow(10, d['digits_min']- 1)) - 1
            range_to = int(math.pow(10, d['digits_max'])) - 1

            n = randint(range_from, range_to)

            if d['negatives']:
                if randint(1, 100) % 2 == 1:
                    n *= -1

            a.append(str(n))

            x = len(d['operations']) - 1
            op = d['operations'][randint(0, x)]

            a.append(op)

        if d['level'] == 1:
            a.append("1")
        else:
            a.pop()

        self.items = a

    def format_challenge(self) -> str:
        text = " ".join(self.items)
        if not self.show_numbers:
            text = re.sub('.', '-', text)

        return text

    def format_answer(self, answer: str, for_display: bool) -> str:
        d = load_settings(self.view_id)
        answer = re.sub(r'\.0$', '', answer)

        if answer.find('.') != -1:
            digits = re.compile('(\\.[0-9]{1,' + str(d['solve_frac_dec']) + '}).*')
            s = re.sub(digits, '\\1', answer)
            if for_display and len(s) < len(answer):
                s = "~" + s
            answer = s

        if for_display:
            answer = "\n= " + answer

        return answer

    def generate_answer(self) -> str:
        if len(self.items) > 0:
            expr = " ".join(self.items)
            answer = str(eval(expr, {'__builtins__':None}))
            return answer
        else:
            return ""


class PreferencesView(PreferencesInterface):
    def save_settings(self):
        d = load_settings(self.view_id)

        for k in ['digits_min', 'digits_max', 'level_max', 'ch_per_level', 'solve_frac_dec']:
            d[k] = int(self.inputs[k].content)

        s = self.inputs['operations'].content
        s = re.sub(r'([^ ])', '\\1 ', s).strip()
        s = re.sub(r'  +', ' ', s)
        ops = s.split(' ')

        d['operations'] = ops

        if self.inputs['negatives'].content == "True":
            d['negatives'] = True
        else:
            d['negatives'] = False

        db.save_settings(self.view_id, json.dumps(d))

    def setup_labels_inputs(self):
        d = load_settings(self.view_id)

        self.labels['digits_min'] = FormLabel(label="Digits min:")
        self.labels['digits_max'] = FormLabel(label="Digits max:")
        self.labels['level_max'] = FormLabel(label="Level max:")
        self.labels['ch_per_level'] = FormLabel(label="Challenges per level:")
        self.labels['operations'] = FormLabel(label="Operations (+ - / *):")
        self.labels['negatives'] = FormLabel(label="Negatives:")
        self.labels['solve_frac_dec'] = FormLabel(label="Solve fractions to decimals:")

        for k in ['digits_min', 'digits_max', 'level_max', 'ch_per_level']:
            self.inputs[k] = InputText(
                label=k,
                content=str(d[k]),
                allow_regex=r'[0-9]',
                input_height=1,
            )

        self.inputs['operations'] = InputText(
            label='operations',
            content=" ".join(d['operations']),
            allow_regex=r'[\+\-\*/ ]',
            input_height=1,
        )

        self.inputs['negatives'] = InputText(
            label='negatives',
            content=str(d['negatives']),
            is_bool=True,
            input_height=1,
        )

        self.inputs['solve_frac_dec'] = InputText(
            label='solve_frac_dec',
            content=str(d['solve_frac_dec']),
            allow_regex=r'[0-9]',
            input_height=1,
        )

        for idx, k in enumerate(self.inputs.keys()):
            self.grid.add_row(f"r{idx+2}", size=1)
            self.grid.add_widget(self.labels[k])
            self.grid.add_widget(self.inputs[k])


class MathArithmeticView(ChallengeInterface):
    def init_view_id(self):
        self.view_id = VIEW_ID

    def init_components(self):
        self.preferences_view = PreferencesView(self.view_id)

        self.footer = Footer()
        self.footer.level = self.current_level

        self.show_numbers = ShowNumbers(self.view_id)
        self.input_answer = InputAnswer(self.get_instruction())

    def get_instruction(self) -> str:
        return "Calculate the expression, then type the result."

    def get_preferences_view(self):
        self.preferences_view = PreferencesView(self.view_id)
        return self.preferences_view
