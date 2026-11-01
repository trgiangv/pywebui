# -*- coding: utf-8 -*-
"""Install and heal the packages of the browser transport for a CPython interpreter.

Everything goes through ``System.Diagnostics.Process``, so this runs the same
under IronPython and under CPython. The target interpreter is only started as
a child process.

The packages live in a folder of their own, ``packages_dir(tag)``, never in the
interpreter's ``site-packages``: other tools share that one. Healing is then
deleting the folder and installing again. An embeddable interpreter
(``python312._pth``) does not put its own ``Lib/site-packages`` on ``sys.path``,
so ``pip`` is started with that folder added.
"""

from __future__ import print_function, division

import glob
import os
import shutil

from pywebui.compat import List, Optional, Tuple

# starlette 0.51 is the first with CORSMiddleware(allow_private_network=...).
# fastapi brings starlette and pydantic, but not uvicorn.
HTTP_REQUIREMENTS = ("fastapi", "starlette>=0.51", "uvicorn", "pydantic>=2.9")

_HERE = os.path.dirname(os.path.abspath(__file__))
_CHECK_SCRIPT = os.path.join(_HERE, "_check.py")
_TAG = "import sys; print('cp{0}{1}'.format(*sys.version_info[:2]))"
_RUN_PIP = (
    "import runpy, sys; sys.path.append(sys.argv.pop(1)); "
    "runpy.run_module('pip', run_name='__main__', alter_sys=True)"
)


def packages_dir(tag):
    # type: (str) -> str
    """Where the packages for the interpreter with this ``cpXY`` tag are installed."""
    return os.path.join(os.environ["LOCALAPPDATA"], "pyWebUI", "packages", tag)


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
    return output.split()


def ensure_packages(python_exe, requirements):
    # type: (str, List[str]) -> Tuple[bool, str]
    """Make ``requirements`` importable from ``packages_dir`` for ``python_exe``.

    ``requirements`` are ``name`` or ``name>=minimum``. A package that is missing,
    too old or fails to import deletes the folder and installs everything again.
    Returns ``(ok, message)``; ``message`` is the pip output when it failed.
    """
    folder = packages_dir(_tag(python_exe))
    if os.path.isdir(folder) and not _unmet(python_exe, folder, requirements):
        return True, "healthy"
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    site_packages = os.path.join(os.path.dirname(python_exe), "Lib", "site-packages")
    code, output = _run(
        python_exe,
        ["-c", _RUN_PIP, site_packages, "install", "--disable-pip-version-check", "--target", folder]
        + list(requirements),
    )
    if code != 0:
        return False, output
    still = _unmet(python_exe, folder, requirements)
    if still:
        return False, "still unmet after install: {0}".format(" ".join(still))
    return True, "installed {0} into {1}".format(" ".join(requirements), folder)
