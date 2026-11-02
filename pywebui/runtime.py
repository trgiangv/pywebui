# -*- coding: utf-8 -*-
"""Install and heal the packages of the browser transport for a CPython interpreter.

Everything goes through ``System.Diagnostics.Process``, so this runs the same
under IronPython and under CPython. The target interpreter is only started as
a child process.

The packages live in a folder of their own, ``packages_dir(tag, group)``, never in the
interpreter's ``site-packages``: other tools share that one. A group is one
caller's set of requirements, installed and replaced as a whole, so callers with
independent lists use different groups and never remove each other's packages.
Every group folder the code needs must be on the interpreter's ``sys.path``
(``embed.start(sys_path=...)``). An embeddable interpreter
(``python312._pth``) does not put its own ``Lib/site-packages`` on ``sys.path``,
so ``pip`` is started with that folder added.
"""

from __future__ import print_function, division

import glob
import os
import shutil

from pywebui.compat import List, Optional, Tuple

# PEP 508 strings, the form of a PEP 723 dependency. Floors are the versions current when
# they were set; raise them when the code starts to need something newer.
# fastapi brings starlette and pydantic, but not uvicorn.
# packaging reads the specifiers, so it is always part of the list.
HTTP_REQUIREMENTS = ("fastapi>=0.162.0", "uvicorn>=0.54.0", "packaging>=26.3")

DEFAULT_GROUP = "pywebui"

_HERE = os.path.dirname(os.path.abspath(__file__))
_CHECK_SCRIPT = os.path.join(_HERE, "_check.py")
_TAG = "import sys; print('cp{0}{1}'.format(*sys.version_info[:2]))"
_RUN_PIP = (
    "import runpy, sys; sys.path.append(sys.argv.pop(1)); "
    "runpy.run_module('pip', run_name='__main__', alter_sys=True)"
)


_FETCH_PIP = (
    "import json, sys, urllib.request; "
    "files = json.load(urllib.request.urlopen('https://pypi.org/pypi/pip/json'))['urls']; "
    "url = next(f['url'] for f in files if f['packagetype'] == 'bdist_wheel'); "
    "urllib.request.urlretrieve(url, sys.argv[1])"
)


def packages_dir(tag, group=DEFAULT_GROUP):
    # type: (str, str) -> str
    """Where ``group``'s packages for the interpreter with this ``cpXY`` tag are installed."""
    return os.path.join(os.environ["LOCALAPPDATA"], "pywebui", "packages", group, tag)


def find_python(engines_dir, prefix):
    # type: (str, str) -> Optional[str]
    """Newest ``<engines_dir>/<prefix>*/python.exe``, or ``None``."""
    found = sorted(glob.glob(os.path.join(engines_dir, prefix + "*", "python.exe")))
    return found[-1] if found else None


def _run(python_exe, arguments):
    # type: (str, List[str]) -> Tuple[int, str]
    from System.Diagnostics import Process, ProcessStartInfo

    info = ProcessStartInfo(python_exe)
    info.Arguments = " ".join('"{0}"'.format(a) for a in arguments)
    info.UseShellExecute = False
    info.CreateNoWindow = True
    info.RedirectStandardOutput = True
    info.RedirectStandardError = True
    process = Process.Start(info)
    output = process.StandardOutput.ReadToEnd() + process.StandardError.ReadToEnd()
    process.WaitForExit()
    return process.ExitCode, output.strip()


def _tag(python_exe):
    # type: (str) -> str
    code, output = _run(python_exe, ["-I", "-c", _TAG])
    if code != 0:
        raise RuntimeError("cannot read the Python version: {0}".format(output))
    return output


def _unmet(python_exe, folder, requirements):
    # type: (str, str, List[str]) -> List[str]
    code, output = _run(python_exe, ["-I", _CHECK_SCRIPT, "--site", folder] + list(requirements))
    if code != 0:
        raise RuntimeError("requirement check failed: {0}".format(output))
    return output.splitlines()


def _pip_path(python_exe):
    # type: (str) -> str
    """The ``sys.path`` entry that provides ``pip``: the engine's ``site-packages``, or a downloaded wheel."""
    site_packages = os.path.join(os.path.dirname(python_exe), "Lib", "site-packages")
    if os.path.isdir(os.path.join(site_packages, "pip")):
        return site_packages
    wheel = os.path.join(os.environ["LOCALAPPDATA"], "pywebui", "pip.whl")
    if not os.path.isfile(wheel):
        partial = wheel + ".part"
        if not os.path.isdir(os.path.dirname(wheel)):
            os.makedirs(os.path.dirname(wheel))
        code, output = _run(python_exe, ["-I", "-c", _FETCH_PIP, partial])
        if code != 0:
            raise RuntimeError("cannot download pip: {0}".format(output))
        os.rename(partial, wheel)
    return wheel


def ensure_packages(python_exe, requirements, group=DEFAULT_GROUP):
    # type: (str, List[str], str) -> Tuple[bool, str]
    """Make ``requirements`` importable from ``packages_dir(tag, group)`` for ``python_exe``.

    ``requirements`` are PEP 508 strings. A package that is missing, outside its
    specifier or fails to import installs everything again, into a staging folder
    first: the current folder is replaced only after the new one passes the check,
    so a failed install (offline, bad specifier) leaves a working install alone.
    Returns ``(ok, message)``; ``message`` is the pip output when it failed.
    """
    folder = packages_dir(_tag(python_exe), group)
    if os.path.isdir(folder) and not _unmet(python_exe, folder, requirements):
        return True, "healthy"
    staging = folder + ".new"
    if os.path.isdir(staging):
        shutil.rmtree(staging)
    code, output = _run(
        python_exe,
        ["-c", _RUN_PIP, _pip_path(python_exe), "install", "--disable-pip-version-check", "--target", staging]
        + list(requirements),
    )
    if code != 0:
        return False, output
    still = _unmet(python_exe, staging, requirements)
    if still:
        return False, "still unmet after install: {0}".format(" ".join(still))
    previous = folder + ".old"
    if os.path.isdir(previous):
        shutil.rmtree(previous, ignore_errors=True)
    if os.path.isdir(folder):
        os.rename(folder, previous)  # fails, changing nothing, while the interpreter has the packages loaded
    os.rename(staging, folder)
    shutil.rmtree(previous, ignore_errors=True)
    return True, "installed {0} into {1}".format(" ".join(requirements), folder)