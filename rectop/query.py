from operator import ge
from operator import gt
from operator import le
from operator import lt

from . import get

class QueryError(Exception):
    pass


def is_rightof(rect1, rect2):
    return rect1.left > rect2.right

def is_above(rect1, rect2):
    return rect1.bottom < rect2.top

def is_below(rect1, rect2):
    return rect1.top > rect2.bottom

def is_leftof(rect1, rect2):
    return rect1.right < rect2.left

facing_predicate_map = {
    'left': is_leftof,
    'right': is_rightof,
    'top': is_above,
    'bottom': is_below,
}

def is_between_vertical(rect1, rect2):
    return rect1.top <= rect2.bottom and rect1.bottom >= rect2.top

def is_between_horizontal(rect1, rect2):
    return rect1.right >= rect2.left and rect1.left <= rect2.right

def predicate_getter(facing, test_rect):
    """
    Return predication function to filter rect relationships.
    """
    facing_predicate = facing_predicate_map[facing]

    if facing in ('right', 'left'):
        is_between = is_between_vertical
    elif facing in ('top', 'bottom'):
        is_between = is_between_horizontal
    else:
        raise QueryError('Invalid direction %s' % facing)

    def predicate(rect):
        return (
            facing_predicate(rect, test_rect)
            and is_between(rect, test_rect)
        )

    return predicate

def filter_rects(rects, facing, test):
    """
    Filter rects in relation to another rect.
    """
    predicate = predicate_getter(facing, test)
    return filter(predicate, rects)
