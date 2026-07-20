# .venv

Python virtual environment. Isolates project dependencies from your system
Python.

- Created with `python3 -m venv .venv`
- Activate with `source .venv/bin/activate`
- Install packages inside it with `pip install -r requirements.txt`

# **pycache**

Python's bytecode cache directory. When you run `.py` files, Python compiles
them to `.pyc` bytecode for faster loading next time. Auto-generated, safe to
delete, gitignored.

# Python Imports

Works the same for standard library, pip packages, and local code.

```python
# Standard library
import os
import os.path as path
from os import getcwd
from os.path import join, exists

# Installed packages (pip)
import flask
from flask import Flask, Blueprint

# Local modules (your .py files)
import config
from config import Config

# Local packages (your directories with __init__.py)
import app
from app import create_app
from app.routes import api

# Wildcard (avoid — pollutes namespace)
from math import *
```

# **name**

Special Python variable. Every module has it — it holds the module's name.

- When run directly, `__name__` is `"__main__"` (entry point)
- When imported, `__name__` is the module's name

```python
# greet.py
print(__name__)
```

```python
# main.py
import greet
```

- `python greet.py` → prints `__main__`
- `python main.py` → prints `greet`

Flask uses this to locate templates and static files relative to where the app
is defined.
