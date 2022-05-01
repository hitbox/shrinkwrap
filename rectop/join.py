from itertools import combinations
from itertools import tee

from . import get

def is_joinable(r1, r2):
    """
    Return whether two rects are joinable, ie: they are the same or they
    exactly share a side.
    """
    top1, right1, bottom1, left1 = get.sides(r1)
    top2, right2, bottom2, left2 = get.sides(r2)
    return (
        r1 == r2
        or (
            top1 == top2
            and bottom1 == bottom2
            and (right1 == left2 or left1 == right2)
        )
        or (
            left1 == left2
            and right1 == right2
            and (top1 == bottom2 or bottom1 == top2)
        )
    )

def defrag(rects):
    """
    Join rects in-place
    """
    def area(item):
        r1, r2, wrapped = item
        return wrapped.width * wrapped.height

    result = {
        'append': [],
        'remove': [],
    }
    append_ops = result['append']
    remove_ops = result['remove']
    while True:
        # generate rects as-if the operations have been applied
        with_ops = (rect for rect in rects + append_ops if rect not in remove_ops)
        # generate 2-tuples of rects that can be joined
        joinables = (
            (r1, r2) for r1, r2 in combinations(with_ops, 2) if is_joinable(r1, r2)
        )
        # duplicate generator to efficiently test and, if it has joinables,
        # join them
        has_join, joinables = tee(joinables)
        if not any(has_join):
            # nothing to join, done
            break
        # generate 3-tuples of rects and a wrapping rect
        joined = ((r1, r2, get.wrap((r1, r2))) for r1, r2 in joinables)
        # find the largest wrap and the rects that can be removed
        r1, r2, largest_join = sorted(joined, key=area)[-1]
        # replace rects with their wrapping rect
        append_ops.append(largest_join)
        remove_ops.extend([r1, r2])
    return result

def apply(defrag_result, rects):
    """
    Apply the result of defrag.
    """
    for newrect in defrag_result['append']:
        rects.append(newrect)
    for redundant in defrag_result['remove']:
        rects.remove(redundant)
