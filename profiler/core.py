# coding: utf-8
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
# Copyright 2014 Anybox <http://anybox.fr>
# Copyright 2016 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
from contextlib import contextmanager

profile = None
"""The thread-shared profile object.
"""

enabled = False
"""Indicates if the whole profiling functionality is globally active or not.
"""


@contextmanager
def profiling():
    """Thread local profile management, according to the shared :data:`enabled`
    """
    if enabled:
        profile.enable()
    yield

    if enabled:
        profile.disable()
