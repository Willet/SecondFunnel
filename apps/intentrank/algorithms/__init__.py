# coding=utf-8

"""Put all IR algorithms here. All algorithms must accept a <tiles>
as the first positional argument, with all other arguments being kwargs.

All algorithms must return <QuerySet>.
"""
from .utils import filter_tiles
from .ir_magic import ir_magic
from .ir_priority import ir_priority


def ir_all(tiles, *args, **kwargs):
    return tiles


__all__ = [ir_all, ir_magic, ir_priority]
