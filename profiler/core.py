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


enabled_orm_methods = None
profile_orm_methods = None


@contextmanager
def profiling_orm_methods():
    """ORM methods profile management, according to the shared :data:`enabled`
    """
    if enabled_orm_methods:
        profile_orm_methods.enable()
    yield

    if enabled_orm_methods:
        profile_orm_methods.disable()
