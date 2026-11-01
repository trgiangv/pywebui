# -*- coding: utf-8 -*-
"""Errors raised when a transport cannot run in the current runtime."""

from __future__ import print_function, division


class UnsupportedRuntimeError(ImportError):
    """A module needs a different Python runtime than the one importing it."""


class RuntimeAlreadyStartedError(RuntimeError):
    """CPython was started in this process by something that did not release the GIL."""


class MissingDependencyError(ImportError):
    """A module needs packages that are not installed for this interpreter."""
