#!/usr/bin/env python3

import json
import re
import math
from enum import Enum
from typing import List, Optional, TypedDict

import memory_master_mind.db as db

class State(int, Enum):
    SHOW_CHALLENGE = 0
    STARTED_ANSWER = 1
    CORRECT = 2
    WRONG = 3
    SHOW_ANSWER = 4

AppId = "Memory Master Mind"
HomeId = 'Home'
StaticNumId = "Static Number Sequence"
TimedNumId = "Timed Number Sequence"
MathArithId = "Math (Arithmetic)"
QuotesId = "Quotes and Verses"

RE_PUNCT = re.compile(r'[\.\?\!,;:\'"\(\)\/-]')

class AppSettings(TypedDict):
    last_challenge: str
    save_stats: bool
    stats_include_settings: bool
    stats_path: str

def app_default_settings() -> AppSettings:
    return AppSettings(
        # Load Home view for the first time.
        last_challenge = HomeId,
        save_stats = False,
        stats_include_settings = False,
        stats_path = "",
    )

def app_load_settings() -> AppSettings:
    view_id = AppId
    res = db.get_settings(view_id)
    if res:
        d: AppSettings = json.loads(res[2])
        return d
    else:
        d = app_default_settings()
        s = json.dumps(d)
        db.save_settings(view_id, s)
        return d


class Settings(TypedDict):
    digits_min: int
    digits_max: int
    ch_per_level: int
    seconds_per_level: int
    level: int
    level_max: int
    zero_padded: bool
    operations: List[str]
    negatives: bool
    solve_frac_dec: int
    words_max: int
    quotes_path: str
    last_quote_idx: int
    show_first_letter: bool
    primes_are_red: bool

def default_settings(view_id: Optional[str] = None) -> Settings:
    d = Settings(
        digits_min = 1,
        digits_max = 2,
        ch_per_level = 2,
        seconds_per_level = 5,
        level = 2,
        level_max = 999,
        zero_padded = False,
        operations = ["+", "-"],
        negatives = False,
        solve_frac_dec = 1,
        words_max = 999,
        quotes_path = "",
        last_quote_idx = 0,
        show_first_letter=True,
        primes_are_red=True,
    )

    if view_id is not None and view_id == QuotesId:
        d['ch_per_level'] = 1
        d['level_max'] = 10

    return d

def load_settings(view_id: str) -> Settings:
    res = db.get_settings(view_id)
    if res:
        d: Settings = json.loads(res[2])
        return d
    else:
        d = default_settings(view_id)
        s = json.dumps(d)
        db.save_settings(view_id, s)
        return d


class Stats(TypedDict):
    datetime: str
    challenge_name: str
    level: str
    solved_in_secs: str
    first_try: str
    settings: str


def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if (n % i) == 0:
            return False
    return True
