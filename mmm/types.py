#!/usr/bin/env python3

import re
from enum import Enum

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
