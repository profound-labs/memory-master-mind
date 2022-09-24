#!/usr/bin/env python3

from enum import Enum

class State(int, Enum):
    SHOW_CHALLENGE = 0
    STARTED_ANSWER = 1
    CORRECT = 2
    WRONG = 3
    SHOW_ANSWER = 4
