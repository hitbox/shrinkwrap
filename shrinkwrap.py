import argparse
import contextlib
import enum
import operator
import os
import random

from itertools import cycle
from types import SimpleNamespace

with contextlib.redirect_stdout(open(os.devnull, 'w')):
    import pygame

class RectSide(enum.Enum):
    # around the rect order, starting from top

    # NOTE:
    #   Was thinking this is too clever--methods in your Enum. The only example
    #   of the standard library doing this:
    #       * cpython/Lib/ast.py
    #   And only one method, `next`, like this one has.

    top = enum.auto()
    right = enum.auto()
    bottom = enum.auto()
    left = enum.auto()

    def next(self, delta=1):
        """
        Return the next side with wraparound.
        """
        sides = list(self.__class__)
        index = (sides.index(self) + delta) % len(sides)
        return sides[index]

    def adjacents(self):
        """
        Return the two adjacent sides.
        """
        return (self.next(-1), self.next(1))

    def opposite(self):
        return self.next(2)

    def rect_value(self, rect):
        """
        Return the value of side `self` of `rect`.
        """
        return getattr(rect, self.name)

    def line(self, rect):
        """
        Return a pygame.Rect of side `self` of `rect`.
        """
        adjacents = self.adjacents()
        adjacent1, adjacent2 = adjacents
        min_adjacent = min(adjacent.rect_value(rect) for adjacent in adjacents)
        # use the normal like a mask
        topleft = tuple(
            self.rect_value(rect) if normval != 0 else min_adjacent
            for normval in self.normal
        )
        width_or_height = abs(adjacent1.rect_value(rect) - adjacent2.rect_value(rect))
        size = tuple(
            width_or_height if normval == 0 else 0
            for normval in self.normal
        )
        return pygame.Rect(topleft, size)


RectSide.top.normal = (0, -1)
RectSide.right.normal = (1, 0)
RectSide.bottom.normal = (0, 1)
RectSide.left.normal = (-1, 0)

assert RectSide.top.next() == RectSide.right
assert RectSide.right.next() == RectSide.bottom
assert RectSide.bottom.next() == RectSide.left
assert RectSide.left.next() == RectSide.top

assert RectSide.top.opposite() == RectSide.bottom

assert RectSide.top.adjacents() == (RectSide.left, RectSide.right)
assert RectSide.bottom.adjacents() == (RectSide.right, RectSide.left)

assert RectSide.top.rect_value(pygame.Rect(0, 10, 5, 5)) == 10


getsides = operator.attrgetter(*RectSide.__members__)

def rect_random(inside, allow_zero=False):
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
    tops, rights, bottoms, lefts = zip(*map(getsides, rects))
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

def rect_stretch(rect, side, absolute_value):
    """
    Stretch rect to the side value. Usually, setting the value of any of the
    corners of a rect, moves it. This changes the equivalent size value and put
    the opposite side back after resizing.
    """
    opposite_value = side.opposite().rect_value(rect)
    if side in (RectSide.top, RectSide.bottom):
        attr = 'height'
    else:
        attr = 'width'
    diff = abs(absolute_value - side.rect_value(rect))
    setattr(rect, attr, diff)
    setattr(rect, side.opposite().name, opposite_value)

def rect_sample_rects(ns):
    """
    sample - rects
    """
    s = .250
    border = ns.frame.inflate(-ns.frame.width*s, -ns.frame.height*s)
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
    # sample rects to wrap
    ns.rects = rect_sample_rects(ns)
    # pick rect to slide a side of
    ns.selectrectiter = cycle(ns.rects)
    ns.selectrect = next(ns.selectrectiter)
    # slide box from side until collision
    ns.sideiter = cycle(RectSide)
    ns.side = next(ns.sideiter)
    #
    ns.wraprect = rect_wrap(ns.rects)
    ns.barriers = rect_get_barriers(ns.wraprect)
    ns.rects.extend(ns.barriers)
    #
    # rect growing out of one of the other rects
    ns.sliderect = ns.side.line(ns.selectrect)
    #
    ns.drag = None
    ns.hover = None
    UPDATE_SLIDE_RECT(ns)

def loop(ns):
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
        UPDATE_SLIDE_RECT(ns)
    else:
        # next sliderect
        ns.side = next(ns.sideiter)
        print(ns.side)
        ns.sliderect = ns.side.line(ns.selectrect)
        update_wraprect(ns)
        UPDATE_SLIDE_RECT(ns)

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
        ns.sliderect = ns.side.line(ns.selectrect)
        UPDATE_SLIDE_RECT(ns)
    else:
        for rect in ns.rects:
            if rect.collidepoint(ns.event.pos):
                ns.hover = rect
                break
        else:
            ns.hover = None

def update_slide_rect_old(ns):
    opposite_name = ns.side.opposite().name
    adjacent1, adjacent2 = ns.side.adjacents()
    if ns.side in (RectSide.top, RectSide.left):
        compop = operator.lt
    else:
        compop = operator.gt

    if ns.side in (RectSide.top, RectSide.right):
        adjcomp1 = operator.le
        adjcomp2 = operator.ge
    else:
        adjcomp1 = operator.ge
        adjcomp2 = operator.le

    if ns.side in (RectSide.right, RectSide.bottom):
        aggfunc = min
    else:
        aggfunc = max
    agg_opposite = aggfunc(
        (
            getattr(rect, opposite_name)
            for rect in ns.rects
            if compop( getattr(rect, opposite_name), ns.side.rect_value(ns.sliderect) )
            # is in our path
            and adjcomp1(adjacent1.rect_value(rect), adjacent1.opposite().rect_value(ns.sliderect))
            and adjcomp2(adjacent2.rect_value(rect), adjacent2.opposite().rect_value(ns.sliderect))
        ),
        default = None
    )
    if agg_opposite is not None:
        rect_stretch(ns.sliderect, ns.side, agg_opposite)

def update(ns):
    """
    update
    """
    #UPDATE_SLIDE_RECT(ns)
    # for some reason updating the sliderect every frame, loses rects from the
    # "queried" rects.
    # Probably because we modify the sliderect and cause there to be no more
    # other rects "to the X of" it.

def update_wraprect(ns):
    rects = (rect for rect in ns.rects if rect not in ns.barriers)
    tops, rights, bottoms, lefts = zip(*map(getsides, rects))
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
            color = (200,200,10)
        elif ns_rect is ns.sliderect:
            color = (200,10,100)
        else:
            color = (100,)*3
        pygame.draw.rect(ns.screen, color, ns_rect, 1)
        image = ns.font.render(str(ns_rect), True, color)
        image_rect = image.get_rect(center=ns_rect.center)
        if not ns.frame.contains(image_rect):
            # NOTE: Wow, spent a lot of time before realizing you call `clamp`
            # *from* the thing you want clamped; *NOT* the rect doing the
            # clamping.
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

UPDATE_SLIDE_RECT = update_slide_rect_old

if __name__ == '__main__':
    main()
