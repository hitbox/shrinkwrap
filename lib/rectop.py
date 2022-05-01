from itertools import combinations
from itertools import tee
from operator import attrgetter

from .external import pygame

def cut(knife, inside):
    """
    Cut rect `inside` with rect `knife` returning a list of rects.
    """
    # TODO: allow any cut, ie: remove test with clip
    subrects = []
    knife = knife.clip(inside)
    if knife != inside:
        top_height = knife.top - inside.top
        left_width = knife.left - inside.left
        right_width = inside.right - knife.right
        bottom_height = inside.bottom - knife.bottom
        subrects = [
            # upper-left
            pygame.Rect(inside.topleft, (left_width, top_height)),
            # mid-upper
            pygame.Rect((knife.left, inside.top), (knife.width, top_height)),
            # upper-right
            pygame.Rect((knife.right, inside.top), (right_width, top_height)),
            # mid-right
            pygame.Rect((knife.right, knife.top), (right_width, knife.height)),
            # bottom-right
            pygame.Rect((knife.right, knife.bottom), (right_width, bottom_height)),
            # mid-bottom
            pygame.Rect((knife.left, knife.bottom), (knife.width, bottom_height)),
            # bottom-left
            pygame.Rect((inside.left, knife.bottom), (left_width, bottom_height)),
            # mid-left
            pygame.Rect((inside.left, knife.top), (left_width, knife.height)),
        ]
        # remove zero size rects
        # TODO: what happens in negative cartesian space?
        subrects = [rect for rect in subrects if rect.width > 0 and rect.height > 0]
    return subrects

getrectsides = attrgetter('top', 'right', 'bottom', 'left')

def wrap(rectsiter):
    """
    Wrap iterable of rects with one large rect.
    """
    tops, rights, bottoms, lefts = zip(*map(getrectsides, rectsiter))
    top = min(tops)
    right = max(rights)
    bottom = max(bottoms)
    left = min(lefts)
    width = right - left
    height = bottom - top
    return pygame.Rect(left, top, width, height)

def is_joinable(r1, r2):
    """
    Return whether two rects are joinable, ie: they are the same or they
    exactly share a side.
    """
    top1, right1, bottom1, left1 = getrectsides(r1)
    top2, right2, bottom2, left2 = getrectsides(r2)
    return (
        r1 == r2
        or
        (top1 == top2 and bottom1 == bottom2 and (right1 == left2 or left1 == right2))
        or
        (left1 == left2 and right1 == right2 and (top1 == bottom2 or bottom1 == top2))
    )

def defrag(rects):
    """
    Join rects in-place
    """
    def area(rectitem):
        r1, r2, wrapped = rectitem
        return wrapped.width * wrapped.height

    while True:
        # generate 2-tuples of rects that can be joined
        joinables = (rectitem for rectitem in combinations(rects, 2)
                     if is_joinable(*rectitem))
        # duplicate generator to efficiently test and, if it has joinables,
        # join them
        has_join, joinables = tee(joinables)
        if not any(has_join):
            # nothing to join, done
            break
        # generate 3-tuples of rects and a wrapping rect
        joined = ((r1, r2, wrap((r1, r2))) for r1, r2 in joinables)
        # find the largest wrap and the rects that can be removed
        r1, r2, largest_join = sorted(joined, key=area)[-1]
        # replace rects with their wrapping rect
        rects.append(largest_join)
        rects.remove(r1)
        rects.remove(r2)

