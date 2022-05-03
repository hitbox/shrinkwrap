from operator import attrgetter

from .external import pygame

# clockwise sorted list of directions
# arranged such that +2 "around" it is the opposite side.
DIRECTIONS = ['top', 'right', 'bottom', 'left']

sides = attrgetter(*DIRECTIONS)

# NOTE: IDK, starting with topleft does not seem like the starting point of clockwise
corners = attrgetter('topright', 'bottomright', 'bottomleft', 'topleft')

points = attrgetter('midtop', 'topright', 'midright', 'bottomright',
        'midbottom', 'bottomleft', 'midleft', 'topleft')

def adjacent_sides(side):
    """
    Return the two adjacent sides, attribute names.
    """
    i = DIRECTIONS.index(side)
    j = (i - 1) % len(DIRECTIONS)
    k = (i + 1) % len(DIRECTIONS)
    return (DIRECTIONS[j], DIRECTIONS[k])

def opposite_side(side):
    """
    Return the opposite of rect side attribute name.
    """
    i = DIRECTIONS.index(side)
    j = (i + 2) % len(DIRECTIONS)
    return DIRECTIONS[j]

def wrap(rectsiter):
    """
    Wrap iterable of rects with one large rect.
    """
    tops, rights, bottoms, lefts = zip(*map(sides, rectsiter))
    top = min(tops)
    right = max(rights)
    bottom = max(bottoms)
    left = min(lefts)
    width = right - left
    height = bottom - top
    return pygame.Rect(left, top, width, height)
