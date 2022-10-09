#!/usr/bin/env python3

import os
import platform
from pathlib import Path
from dotenv import load_dotenv
import appdirs

load_dotenv()

s = os.getenv('DEV')
if s is not None and s == "True":
    IS_DEV = True
else:
    IS_DEV = False

MMM_PACKAGE_DIR = Path(os.path.dirname(__file__)).absolute()

PACKAGE_QUOTES_PATH = MMM_PACKAGE_DIR.joinpath("assets/quotes.csv")

MARKDOWN_DIR = MMM_PACKAGE_DIR.joinpath("assets/")

s = os.getenv('MMM_DIR')
if s is not None and s != '':
    MMM_DIR = Path(s)
else:
    MMM_DIR = Path(appdirs.user_data_dir('mmm'))

DB_PATH = MMM_DIR.joinpath('appdata.sqlite3')

if not MMM_DIR.exists():
    MMM_DIR.mkdir()

IS_LINUX = (platform.system() == 'Linux')
IS_WINDOWS = (platform.system() == 'Windows')
IS_MAC = (platform.system() == 'Darwin')
