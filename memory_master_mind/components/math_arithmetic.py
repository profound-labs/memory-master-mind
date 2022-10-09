#!/usr/bin/env python3

# Math (Arithmetic)

import re
import math
from random import randint
import json

from rich.text import Text

from memory_master_mind.types import MathArithId, is_prime, load_settings
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

    def format_answer_plain(self) -> str:
        d = load_settings(self.view_id)
        answer = self.generate_answer()
        answer = re.sub(r'\.0$', '', answer)

        if answer.find('.') != -1:
            digits = re.compile('(\\.[0-9]{1,' + str(d['solve_frac_dec']) + '}).*')
            answer = re.sub(digits, '\\1', answer)

        return answer

    def format_answer_rich(self) -> Text:
        d = load_settings(self.view_id)
        answer = self.generate_answer()
        answer = re.sub(r'\.0$', '', answer)

        text = self.format_challenge_rich().append("\n= ")

        if answer.find('.') != -1:
            digits = re.compile('(\\.[0-9]{1,' + str(d['solve_frac_dec']) + '}).*')
            s = re.sub(digits, '\\1', answer)
            if len(s) < len(answer):
                s = "~" + s
            text.append(s)

        elif answer.find('-') != -1:
            if answer.isdigit() and d['primes_are_red'] and is_prime(int(answer)):
                text.append(answer, style="red")
            else:
                text.append(answer)
        else:
            text.append(answer)

        return text

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

        for k in ['digits_min', 'digits_max', 'level_max', 'ch_per_level', 'seconds_per_level', 'solve_frac_dec']:
            d[k] = int(self.inputs[k].content)

        s = self.inputs['operations'].content
        s = re.sub(r'([^ ])', '\\1 ', s).strip()
        s = re.sub(r'  +', ' ', s)
        ops = s.split(' ')

        d['operations'] = ops

        if self.inputs['primes_are_red'].content == "True":
            d['primes_are_red'] = True
        else:
            d['primes_are_red'] = False

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
        self.labels['seconds_per_level'] = FormLabel(label="Seconds per level:")
        self.labels['primes_are_red'] = FormLabel(label="Primes are red:")
        self.labels['operations'] = FormLabel(label="Operations (+ - / *):")
        self.labels['negatives'] = FormLabel(label="Negatives:")
        self.labels['solve_frac_dec'] = FormLabel(label="Solve fractions to decimals:")

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
    def init_attr(self):
        self.view_id = MathArithId
        self.help_md_filename = "math_arithmetic.md"

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
