from contextlib import contextmanager
profile = None
"""The thread-shared profile object.
"""

enabled = False
"""Indicates if the whole profiling functionality is globally active or not.
"""

player_state = 'profiler_player_clear'
"""Indicate the state(css class) of the player:

* profiler_player_clear
* profiler_player_enabled
* profiler_player_disabled
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
