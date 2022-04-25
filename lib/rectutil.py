import enum

from . import rectside
from .external import pygame

class RectPoints(enum.Enum):
    """
    Enumeration of the points, clockwise, around a rect.
    """
    midtop = enum.auto()
    topright = enum.auto()
    midright = enum.auto()
    bottomright = enum.auto()
    midbottom = enum.auto()
    bottomleft = enum.auto()
    midleft = enum.auto()
    topleft = enum.auto()


def iterpoints(rect):
    """
    Iterate important points, clockwise, around a rect; starting at midtop.
    """
    return (getattr(rect, point.name) for point in RectPoints)

def rect_from_points(points):
    """
    :param points: iterable of (x,y) pairs
    """
    xs, ys = zip(*points)
    left, right = min(xs), max(xs)
    top, bottom = min(ys), max(ys)
    width = right - left
    height = bottom - top
    return pygame.Rect(left, top, width, height)

def rect_get(rect, **kwargs):
    """
    Like pygame's `surface.get_rect` for `pygame.Rect`s.
    """
    result = rect.copy()
    for key, val in kwargs.items():
        setattr(result, key, val)
    return result

def rect_get_barriers(rect, limit=None):
    """
    Return list of rect copies that surround the given rect. Like creating four
    walls from the rect.

    :param rect: build four other rects around this one.
    :param limit: tuple(width, height) or numerical for both.
    """
    top, right, bottom, left = (rect.copy() for _ in range(4))
    if limit:
        try:
            width, height = limit
        except TypeError:
            width = height = limit
        top.height = bottom.height = height
        left.width = right.width = width
    top.bottom = rect.top
    right.left = rect.right
    bottom.top = rect.bottom
    left.right = rect.left
    # allow caller to decide container type
    return iter((top, right, bottom, left))

def rect_wrap(rects):
    """
    Return a rect that wraps around the given rects.
    """
    tops, rights, bottoms, lefts = zip(*map(rectside.getsides, rects))
    top = min(tops)
    right = max(rights)
    bottom = max(bottoms)
    left = min(lefts)
    return pygame.Rect(left, top, right - left, bottom - top)
