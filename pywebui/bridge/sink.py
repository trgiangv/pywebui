# -*- coding: utf-8 -*-
"""Where a transport receives envelopes the application produces."""

from __future__ import print_function, division

from pywebui.bridge.envelope import Envelope


class EnvelopeSink(object):
    """Delivers responses and events to the page. Implemented per transport."""

    def send(self, message):
        # type: (Envelope) -> None
        raise NotImplementedError
