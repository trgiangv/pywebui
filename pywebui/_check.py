# -*- coding: utf-8 -*-
"""Requirement check that needs only CPython and ``packaging``.

Run it as a script in the interpreter to inspect:
``python -I _check.py --site DIR "name>=1.2" other``. ``DIR`` goes first on
``sys.path``: an embeddable interpreter does not see its own ``site-packages``.
Each requirement is a PEP 508 string, the same form as a PEP 723 dependency.
It prints the requirements whose package is not installed, has a version outside
the specifier, or fails to import. The import name is the distribution name.
"""

from __future__ import division, print_function

import importlib
import sys
from importlib.metadata import PackageNotFoundError, version


def unmet(requirements):
    """Requirements this interpreter does not meet.

    Without ``packaging`` the specifiers cannot be read, so every requirement is
    reported and the caller installs again.
    """
    try:
        from packaging.requirements import Requirement
    except ImportError:
        return list(requirements)

    result = []
    for text in requirements:
        requirement = Requirement(text)
        try:
            installed = version(requirement.name)
            importlib.import_module(requirement.name.replace("-", "_"))
        except (PackageNotFoundError, ImportError):
            result.append(text)
            continue
        if not requirement.specifier.contains(installed, prereleases=True):
            result.append(text)
    return result


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--site"]:
        sys.path.insert(0, args[1])
        args = args[2:]
    print("\n".join(unmet(args)))