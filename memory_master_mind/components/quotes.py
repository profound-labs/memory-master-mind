#!/usr/bin/env python3

# Quotes

from pathlib import Path
import re
import math
from random import randrange
import json
import csv
from typing import List, Optional, Tuple

from rich.text import Text

from memory_master_mind import PACKAGE_QUOTES_PATH
from memory_master_mind.types import QuotesId, RE_PUNCT, load_settings
import memory_master_mind.db as db
from memory_master_mind.components.footer import Footer
from memory_master_mind.components.form_label import FormLabel
from memory_master_mind.components.input_answer import InputAnswer
from memory_master_mind.components.challenge_interface import ChallengeInterface, ShowChallengeInterface
from memory_master_mind.components.preferences_interface import PreferencesInterface
from memory_master_mind.components.input_text import InputText

QUOTES = []

def init_quotes():
    if len(QUOTES) > 0:
        return
    d = load_settings(QuotesId)
    p = d['quotes_path']
    if p != "" and Path(p).expanduser().exists():
        quotes_path = Path(p).expanduser()
    else:
        quotes_path = PACKAGE_QUOTES_PATH
    with open(quotes_path) as file:
        rows = csv.reader(file, delimiter=",", quotechar='"')
        for r in filter(lambda x: len(x) > 0, rows):
            QUOTES.append(r[0])


class ShowQuote(ShowChallengeInterface):
    hidden_words: List[str] = []
    hidden_words_idx: List[int] = []
    current_quote_idx: Optional[int] = None
    next_quote_idx: Optional[int] = None

    def quote_to_body_and_author(self, quote: str) -> List[str]:
        re_author = re.compile(r'(\([^\)]+\))$')
        m = re.search(re_author, quote)
        if m is not None:
            author = m.group(1)
            body = quote.replace(author, '').strip()
        else:
            lines = quote.split("\n")
            if len(lines) > 1:
                body = "\n".join(lines[0:-1]).strip()
                author = lines[-1].strip()
            else:
                body = "\n".join(lines).strip()
                author = "Unknown"

        return [body, author]

    def quote_body_split(self, quote: str) -> List[str]:
        (body, _) = self.quote_to_body_and_author(quote)

        a = []
        for line in body.split("\n"):
            for w in line.split(" "):
                a.append(w)
            a.append("\n")

        return a

    def quote_words_join(self, words: List[str]) -> str:
        quote = " ".join(words)
        quote = re.sub(r'\n +', '\n', quote)
        return quote.strip()

    def quotes_words_max(self, words_max: int) -> List[str]:
        def quote_select(x: str) -> bool:
            n = len(self.quote_body_split(x))
            return (n <= words_max)

        ret = list(filter(quote_select, QUOTES))

        return ret

    def get_new_quote(self, quotes: List[str]) -> Tuple[int, str]:
        idx = randrange(0, len(quotes))
        if len(quotes) > 1:
            while idx == self.current_quote_idx:
                idx = randrange(0, len(quotes))

        quote = quotes[idx]

        return (idx, quote)

    def new_challenge(self, regenerate: bool = True):
        d = load_settings(self.view_id)
        level = d['level']
        words_max = d['words_max']

        if level <= 2 and words_max > 20:
            words_max = 20

        quotes = self.quotes_words_max(words_max)

        if self.next_quote_idx is not None and self.next_quote_idx < len(quotes):
            quote = quotes[self.next_quote_idx]
            self.current_quote_idx = self.next_quote_idx
            self.next_quote_idx = None
            self.items = [quote]
        elif regenerate:
            idx, quote = self.get_new_quote(quotes)
            self.current_quote_idx = idx
            self.items = [quote]
        else:
            quote = self.items[0]

        self.hidden_words = []
        self.hidden_words_idx = []

        if self.current_quote_idx is not None:
            d['last_quote_idx'] = self.current_quote_idx
            db.save_settings(self.view_id, json.dumps(d))

        words = self.quote_body_split(quote)
        words_w_idx = list(filter(lambda x: x[1] not in ["\n", "/", "-", "--"], list(enumerate(words))))

        # Hide level*10 percent of words
        if level >= 10:
            total_hidden = len(words_w_idx)
        else:
            total_hidden = math.floor(len(words_w_idx) * (level/10))

        if total_hidden == 0:
            total_hidden = 1

        while len(self.hidden_words_idx) < total_hidden:
            n = randrange(0, len(words_w_idx))
            idx, i = words_w_idx[n]
            if idx not in self.hidden_words_idx and i not in ["\n", "/", "-", "--"]:
                self.hidden_words_idx.append(idx)
                words_w_idx.remove(words_w_idx[n])

        self.hidden_words_idx.sort()
        for i in self.hidden_words_idx:
            w = re.sub(RE_PUNCT, '', words[i])
            self.hidden_words.append(w)

    def format_challenge_plain(self) -> str:
        (body, author) = self.quote_to_body_and_author(self.items[0])

        words = self.quote_body_split(self.items[0])
        if not self.show_numbers:
            d = load_settings(self.view_id)
            for i in self.hidden_words_idx:
                if len(words[i]) > 2 and d['show_first_letter']:
                    words[i] = words[i][0] + re.sub('.', '-', words[i][1:])
                else:
                    words[i] = re.sub('.', '-', words[i])

        body = self.quote_words_join(words)

        if author.find('(') == -1:
            quote = body + "\n\n" + author
        else:
            quote = body + " " + author

        return quote

    def format_challenge_rich(self) -> Text:
        return Text(self.format_challenge_plain())

    def generate_answer(self) -> str:
        return " ".join(self.hidden_words)

    def format_answer_plain(self) -> str:
        return self.generate_answer()

    def format_answer_rich(self) -> Text:
        return self.format_challenge_rich()


class PreferencesView(PreferencesInterface):
    def save_settings(self):
        d = load_settings(self.view_id)

        for k in ['level_max', 'ch_per_level', 'words_max']:
            d[k] = int(self.inputs[k].content)

        d['quotes_path'] = self.inputs['quotes_path'].content

        if self.inputs['show_first_letter'].content == "True":
            d['show_first_letter'] = True
        else:
            d['show_first_letter'] = False

        db.save_settings(self.view_id, json.dumps(d))

        QUOTES.clear()
        init_quotes()

    def setup_labels_inputs(self):
        d = load_settings(self.view_id)

        self.labels['level_max'] = FormLabel(label="Level max:")
        self.labels['ch_per_level'] = FormLabel(label="Challenges per level:")
        self.labels['words_max'] = FormLabel(label="Words max:")
        self.labels['show_first_letter'] = FormLabel(label="Show first letter:")
        self.labels['quotes_path'] = FormLabel(label="Quotes CSV file path:")

        for k in ['level_max', 'ch_per_level', 'words_max']:
            self.inputs[k] = InputText(
                label=k,
                content=str(d[k]),
                allow_regex=r'[0-9]',
                input_height=1,
            )

        self.inputs['show_first_letter'] = InputText(
            label='show_first_letter',
            content=str(d['show_first_letter']),
            is_bool=True,
            input_height=1,
        )

        self.inputs['quotes_path'] = InputText(
            label='quotes_path',
            content=str(d['quotes_path']),
            is_text=True,
            input_height=1,
        )

        for idx, k in enumerate(self.inputs.keys()):
            self.grid.add_row(f"r{idx+2}", size=1)
            self.grid.add_widget(self.labels[k])
            self.grid.add_widget(self.inputs[k])


class QuotesView(ChallengeInterface):
    def init_attr(self):
        self.view_id = QuotesId
        self.help_md_filename = "quotes_and_verses.md"

    def init_components(self):
        init_quotes()

        self.preferences_view = PreferencesView(self.view_id)

        self.footer = Footer()
        self.footer.level = self.current_level

        self.show_numbers = ShowQuote(self.view_id)

        d = load_settings(self.view_id)
        self.show_numbers.next_quote_idx = d['last_quote_idx']

        self.input_answer = InputAnswer(self.get_instruction())
        self.input_answer.only_numbers = False

    def get_instruction(self) -> str:
        return "Type the hidden words. Caps, punctuation, linebreaks are optional."

    def get_preferences_view(self):
        self.preferences_view = PreferencesView(self.view_id)
        return self.preferences_view
