import argparse
import operator
import random

from itertools import cycle
from operator import attrgetter
from types import SimpleNamespace

from lib import rectside
from lib.external import pygame
from lib.rectside import RectSide

class ShrinkWrapError(Exception):
    pass


def rect_random(inside, allow_zero=False):
    raise NotImplementedError('TODO: efficient random placement inside empty space.')
    while True:
        left, right = sorted(random.randrange(inside.left, inside.right) for _ in range(2))
        if allow_zero or left != right:
            break
    while True:
        top, bottom = sorted(random.randrange(inside.top, inside.bottom) for _ in range(2))
        if allow_zero or top != bottom:
            break
    return pygame.Rect(left, top, right - left, bottom - top)

def rect_get(rect, **kwargs):
    result = rect.copy()
    for key, val in kwargs.items():
        setattr(result, key, val)
    return result

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

def rect_get_barriers(rect):
    """
    Return list of rect copies that surround the given rect.
    """
    top, right, bottom, left = (rect.copy() for _ in range(4))
    top.bottom = rect.top
    right.left = rect.right
    bottom.top = rect.bottom
    left.right = rect.left
    return [top, right, bottom, left]

def rect_stretch_side(rect, side, absolute_value):
    """
    Stretch rect to the side value. Usually, setting the value of any of the
    corners of a rect, moves it. This changes the equivalent size value and put
    the opposite side back after resizing.
    """
    opposite_value = side.opposite().side_value(rect)
    if side in (RectSide.top, RectSide.bottom):
        attr = 'height'
    else:
        attr = 'width'
    diff = abs(absolute_value - side.side_value(rect))
    setattr(rect, attr, diff)
    setattr(rect, side.opposite().name, opposite_value)

def rect_shrink(rect, *scale):
    if not (1 <= len(scale) <= 2):
        raise ShrinkWrapError('requires one or two arguments.')
    if len(scale) == 1:
        scale = (scale[0],)*2
    sw, sh = scale
    return rect.inflate(-rect.width*sw, -rect.height*sh)

def rect_sample_rects(ns):
    """
    sample - rects
    """
    s = .250
    border = rect_shrink(ns.frame, s)
    rects = [
        rect_get(border, size=(100,)*2, center=border.center),
        rect_get(border, size=(50,)*2, topleft=border.topleft),
        rect_get(border, size=(50,)*2, bottomright=border.bottomright),
        rect_get(border, size=(25,)*2, midbottom = border.midbottom),
    ]
    return rects

def post_quit():
    """
    post quit event
    """
    pygame.event.post(pygame.event.Event(pygame.QUIT))

def init(ns):
    """
    Initialize rects and other objects.
    """
    # sample rects to wrap
    ns.rects = rect_sample_rects(ns)
    # pick rect to slide a side of
    ns.selectables = list(ns.rects)
    ns.selectrectiter = cycle(ns.selectables)
    ns.selectrect = next(ns.selectrectiter)
    # slide box from side until collision
    ns.sideiter = cycle(RectSide)
    ns.slideside = next(ns.sideiter)
    #
    ns.wraprect = rect_wrap(ns.rects)
    ns.barriers = rect_get_barriers(ns.wraprect)
    ns.rects.extend(ns.barriers)
    #
    # rect growing out of one of the other rects
    ns.sliderect = ns.slideside.side_rect(ns.selectrect)
    #
    ns.drag = None
    ns.hover = None
    update_slide_rect(ns)

def loop(ns):
    """
    main loop
    """
    running = True
    while running:
        ns.elapsed = ns.clock.tick(ns.frames_per_second)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                ns.event = event
                ns.on_event(ns)
        # update
        ns.update(ns)
        ns.draw(ns)

def on_event(ns):
    """
    event
    """
    if ns.event.type == pygame.KEYDOWN:
        on_event_keydown(ns)
    elif ns.event.type == pygame.MOUSEBUTTONDOWN:
        on_event_mousebuttondown(ns)
    elif ns.event.type == pygame.MOUSEBUTTONUP:
        on_event_mousebuttonup(ns)
    elif ns.event.type == pygame.MOUSEMOTION:
        on_event_mousemotion(ns)

def on_event_keydown(ns):
    """
    event - keydown
    """
    if ns.event.key in (pygame.K_ESCAPE, pygame.K_q):
        post_quit()
    elif ns.event.key == pygame.K_SPACE:
        # next selectrect
        ns.selectrect = next(ns.selectrectiter)
        update_wraprect(ns)
        update_slide_rect(ns)
    else:
        # next sliderect on any other key
        ns.slideside = next(ns.sideiter)
        ns.sliderect = ns.slideside.side_rect(ns.selectrect)
        update_wraprect(ns)
        update_slide_rect(ns)

def on_event_mousebuttondown(ns):
    for rect in ns.rects:
        if rect.collidepoint(ns.event.pos):
            ns.drag = rect
            break
        else:
            ns.drag = None

def on_event_mousebuttonup(ns):
    ns.drag = None

def on_event_mousemotion(ns):
    if ns.drag:
        dx, dy = ns.event.rel
        ns.drag.x += dx
        ns.drag.y += dy
        update_wraprect(ns)
        ns.sliderect = ns.slideside.side_rect(ns.selectrect)
        update_slide_rect(ns)
    else:
        # indicate hovering a selectable
        for rect in ns.selectables:
            if rect.collidepoint(ns.event.pos):
                ns.hover = rect
                break
        else:
            ns.hover = None

class PathThingy:
    """
    Thingy to compare the sliderect's sliding side's path, to another rect and
    determine if the other rect would collide if the sliding side went to
    infinity.
    """
    # TODO: class name

    def __init__(self, adjacent1, adjacent2, adjcomp1, adjcomp2):
        self.adjacent1 = adjacent1
        self.adjacent2 = adjacent2
        self.adjcomp1 = adjcomp1
        self.adjcomp2 = adjcomp2
        self.opposite1 = self.adjacent1.opposite()
        self.opposite2 = self.adjacent2.opposite()

    def is_inside_path(self, sliderect, rect):
        """
        The rect path swept out by side

        ex. For a given rect, other, and sweeping side "right" of sliderect:

        other's top is above sliderect's bottom, and other's bottom is below
        sliderect's top.

            other.top    <= sliderect.bottom
        and other.bottom >= sliderect.top
        """
        rect_adjacent1 = self.adjacent1.side_value(rect)
        rect_adjacent2 = self.adjacent2.side_value(rect)
        slide_opposite1 = self.opposite1.side_value(sliderect)
        slide_opposite2 = self.opposite2.side_value(sliderect)
        return (
            self.adjcomp1(rect_adjacent1, slide_opposite1)
            and self.adjcomp2(rect_adjacent2, slide_opposite2)
        )


def update_slide_rect(ns):
    opposite_name = ns.slideside.opposite().name
    adjacent1, adjacent2 = ns.slideside.adjacents()
    if ns.slideside in (RectSide.top, RectSide.left):
        compop = operator.lt
    else:
        compop = operator.gt

    if ns.slideside in (RectSide.top, RectSide.right):
        adjcomp1 = operator.le
        adjcomp2 = operator.ge
    else:
        adjcomp1 = operator.ge
        adjcomp2 = operator.le

    if ns.slideside in (RectSide.right, RectSide.bottom):
        aggragate = min
    else:
        aggragate = max

    paththingy = PathThingy(adjacent1, adjacent2, adjcomp1, adjcomp2)

    opposite_side = attrgetter(opposite_name)

    def predicate(rect):
        return (
            rect is not ns.sliderect
            and compop(opposite_side(rect), ns.slideside.side_value(ns.sliderect))
            and paththingy.is_inside_path(ns.sliderect, rect)
        )

    opposite_sides = map(opposite_side, filter(predicate, ns.rects))
    agg_opposite = aggragate(opposite_sides, default=None)
    if agg_opposite is not None:
        rect_stretch_side(ns.sliderect, ns.slideside, agg_opposite)

def update(ns):
    """
    update
    """
    #update_slide_rect(ns)
    # for some reason updating the sliderect every frame, loses rects from the
    # "queried" rects.
    # Probably because we modify the sliderect and cause there to be no more
    # other rects "to the X of" it.

def update_wraprect(ns):
    rects = (rect for rect in ns.rects if rect not in ns.barriers)
    tops, rights, bottoms, lefts = zip(*map(rectside.getsides, rects))
    top = min(tops)
    right = max(rights)
    bottom = max(bottoms)
    left = min(lefts)
    ns.wraprect.top = top
    ns.wraprect.left = left
    ns.wraprect.width = right - left
    ns.wraprect.height = bottom - top
    #
    for rect in ns.barriers:
        rect.size = ns.wraprect.size
    top, right, bottom, left = ns.barriers
    top.midbottom = ns.wraprect.midtop
    right.midleft = ns.wraprect.midright
    bottom.midtop = ns.wraprect.midbottom
    left.midright = ns.wraprect.midleft

def draw(ns):
    """
    draw
    """
    # clear screen
    ns.screen.fill((0,)*3)
    pygame.draw.rect(ns.screen, (30,)*3, ns.wraprect, 1)

    # XXX
    # 2022-01-28
    # Ok, the update function now works in a fairly general fashion, for any of
    # the four sides.

    # draw rects
    for ns_rect in ns.rects + [ns.sliderect]:
        if ns_rect is ns.hover:
            # TODO: only hover/highlight draggable rects.
            color = (200,200,10)
        elif ns_rect is ns.sliderect:
            color = (200,10,100)
        else:
            color = (100,)*3
        pygame.draw.rect(ns.screen, color, ns_rect, 1)
        image = ns.font.render(str(ns_rect), True, color)
        image_rect = image.get_rect(center=ns_rect.center)
        if not ns.frame.contains(image_rect):
            # NOTE: rect_to_clamp.clamp(rect_to_clamp_inside_of)
            image_rect = image_rect.clamp(ns.frame)
        ns.screen.blit(image, image_rect)
        # debug rect
        #pygame.draw.rect(ns.screen, (200,30,30), image_rect, 1)

    pygame.display.flip()

def main(argv=None):
    """
    Shrink-wrap a group of pygame.Rect rects.
    """
    parser = argparse.ArgumentParser(description=main.__doc__)
    args = parser.parse_args(argv)

    ns = SimpleNamespace()

    pygame.font.init()

    ns.screen = pygame.display.set_mode((800,)*2)
    ns.frame = ns.screen.get_rect()
    ns.clock = pygame.time.Clock()
    ns.frames_per_second = 60
    ns.font = pygame.font.Font(None, 24)

    ns.on_event = on_event
    ns.update = update
    ns.draw = draw

    init(ns)
    loop(ns)

if __name__ == '__main__':
    main()
