# -*- coding: utf-8 -*-
"""Requirement check that needs only the standard library of CPython.

Run it as a script in the interpreter to inspect:
``python -I _check.py --site DIR "name>=1.2" other``. ``DIR`` goes first on
``sys.path``: an embeddable interpreter does not see its own ``site-packages``.
It prints the specs that are missing, older than their minimum, or that fail to import.
The import name is the distribution name.
"""

from __future__ import division, print_function

import importlib
import re
import sys
from importlib.metadata import PackageNotFoundError, version


def _numbers(text):
    return tuple(int(n) for n in re.findall(r"\d+", text))


def unmet(specs):
    """Specs of the form ``name`` or ``name>=minimum`` that this interpreter does not meet."""
    result = []
    for spec in specs:
        name, _, minimum = spec.partition(">=")
        try:
            installed = version(name)
        except PackageNotFoundError:
            result.append(spec)
            continue
        if minimum and _numbers(installed) < _numbers(minimum):
            result.append(spec)
            continue
        try:
            importlib.import_module(name)
        except ImportError:
            result.append(spec)
    return result


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--site"]:
        sys.path.insert(0, args[1])
        args = args[2:]
    print("\n".join(unmet(args)))
