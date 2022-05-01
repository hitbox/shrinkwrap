import argparse
import operator
import pickle
import random

from itertools import cycle
from operator import attrgetter
from types import SimpleNamespace

from lib import rectside
from lib.external import pygame
from lib.rectside import RectSide
from lib.rectutil import rect_get
from lib.rectutil import rect_get_barriers
from lib.rectutil import rect_wrap

class ShrinkWrapError(Exception):
    pass


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
        update_slide_rect(ns.sliderect, ns.slideside, ns.rects)
    else:
        # next sliderect on any other key
        ns.slideside = next(ns.sideiter)
        ns.sliderect = ns.slideside.side_rect(ns.selectrect)
        update_wraprect(ns)
        update_slide_rect(ns.sliderect, ns.slideside, ns.rects)

def on_event_mousebuttondown(ns):
    if ns.event.button == 1:
        # click to drag rect
        screen_pos = ns.event.pos
        world_pos = (
            screen_pos[0] - ns.camera.x,
            screen_pos[1] - ns.camera.y,
        )
        for rect in ns.rects + [ns.selectrect]:
            if rect.collidepoint(world_pos):
                ns.drag = rect
                break
            else:
                ns.drag = None
    elif ns.event.button == 2:
        # click move camera
        ns.drag_camera = True

def on_event_mousebuttonup(ns):
    ns.drag = None
    ns.drag_camera = None

def on_event_mousemotion(ns):
    if ns.drag:
        # dragging rect
        dx, dy = ns.event.rel
        ns.drag.x += dx
        ns.drag.y += dy
        update_wraprect(ns)
        ns.sliderect = ns.slideside.side_rect(ns.selectrect)
        update_slide_rect(ns.sliderect, ns.slideside, ns.rects)
    elif ns.drag_camera:
        # drag/move camera
        ns.camera.move_ip(*ns.event.rel)
    else:
        # indicate hovering a selectable
        screen_pos = ns.event.pos
        world_pos = (
            screen_pos[0] - ns.camera.x,
            screen_pos[1] - ns.camera.y,
        )
        for rect in ns.selectables:
            if rect.collidepoint(world_pos):
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
    #       * remove all this dependency and just use the well known attributes
    #         of rects.

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


def update_slide_rect(sliderect, slideside, rects):
    opposite_name = slideside.opposite().name
    adjacent1, adjacent2 = slideside.adjacents()
    if slideside in (RectSide.top, RectSide.left):
        compop = operator.lt
    else:
        compop = operator.gt

    if slideside in (RectSide.top, RectSide.right):
        adjcomp1 = operator.le
        adjcomp2 = operator.ge
    else:
        adjcomp1 = operator.ge
        adjcomp2 = operator.le

    if slideside in (RectSide.right, RectSide.bottom):
        aggragate = min
    else:
        aggragate = max

    paththingy = PathThingy(adjacent1, adjacent2, adjcomp1, adjcomp2)

    opposite_side = attrgetter(opposite_name)

    def predicate(rect):
        return (
            rect is not sliderect
            and compop(opposite_side(rect), slideside.side_value(sliderect))
            and paththingy.is_inside_path(sliderect, rect)
        )

    opposite_sides = map(opposite_side, filter(predicate, rects))
    agg_opposite = aggragate(opposite_sides, default=None)
    if agg_opposite is not None:
        # in-place op
        rect_stretch_side(sliderect, slideside, agg_opposite)

def update(ns):
    """
    update
    """

def update_wraprect(ns):
    if ns.wraprect:
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
        if len(ns.barriers) == 4:
            top, right, bottom, left = ns.barriers
            top.width = bottom.width = ns.wraprect.width
            left.height = right.height = ns.wraprect.height
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

    if ns.wraprect:
        # draw the wrap rect
        pygame.draw.rect(ns.screen, (30,)*3, ns.wraprect.move(*ns.camera.topleft), 1)

    # draw rects
    for ns_rect in ns.rects + [ns.sliderect, ns.selectrect]:
        if ns_rect is ns.selectrect:
            color = (200,10,10)
        elif ns_rect is ns.hover:
            # TODO: only hover/highlight draggable rects.
            color = (200,200,10)
        elif ns_rect is ns.sliderect:
            color = (200,10,100)
        else:
            color = (100,)*3
        pygame.draw.rect(ns.screen, color, ns_rect.move(*ns.camera.topleft), 1)
        if ns.rect_labels:
            # label
            image = ns.font.render(str(ns_rect), True, color)
            image_rect = image.get_rect(center=ns_rect.center)
            if not ns.frame.contains(image_rect):
                # NOTE: rect_to_clamp.clamp(rect_to_clamp_inside_of)
                image_rect = image_rect.clamp(ns.frame)
            ns.screen.blit(image, image_rect.move(*ns.camera.topleft))
            # debug rect
            #pygame.draw.rect(ns.screen, (200,30,30), image_rect, 1)

    pygame.display.flip()

def init(ns):
    """
    Initialize rects and other objects.
    """
    # pick rect to slide a side of
    ns.selectables = [rect_get(ns.frame, size=(10,10), center=ns.frame.center)]
    ns.selectrectiter = cycle(ns.selectables)
    ns.selectrect = next(ns.selectrectiter)
    # slide box from side until collision
    ns.sideiter = cycle(RectSide)
    ns.slideside = next(ns.sideiter)
    #
    # rect growing out of one of the other rects
    ns.sliderect = ns.slideside.side_rect(ns.selectrect)
    #
    ns.drag = None
    ns.hover = None
    update_slide_rect(ns.sliderect, ns.slideside, ns.rects)
    #
    ns.drag_camera = None

def main(argv=None):
    """
    Shrink-wrap a group of pygame.Rect rects.
    """
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('--rects', help='Load rects from pickle.')
    args = parser.parse_args(argv)

    ns = SimpleNamespace()

    pygame.font.init()

    ns.screen = pygame.display.set_mode((800,)*2)
    ns.frame = ns.screen.get_rect()
    ns.camera = ns.frame.copy()
    ns.clock = pygame.time.Clock()
    ns.frames_per_second = 60
    ns.font = pygame.font.Font(None, 24)
    ns.rect_labels = False

    ns.on_event = on_event
    ns.update = update
    ns.draw = draw

    ns.wraprect = None
    ns.barriers = []
    if args.rects:
        with open(args.rects, 'rb') as fp:
            ns.rects = [pygame.Rect(*rectuple) for rectuple in pickle.load(fp)]
    else:
        ns.rect_labels = True
        ns.rects = rect_sample_rects(ns)

    # build walls
    ns.wraprect = rect_wrap(ns.rects).inflate(50,50)
    ns.barriers = list(rect_get_barriers(ns.wraprect, 10))
    ns.rects.extend(ns.barriers)

    init(ns)
    loop(ns)

if __name__ == '__main__':
    main()

# 2022-05-01
# * cleaned up things and put stuff in demos folder.
# * the only thing left inside here, in shrinkwrap.py, is the projection of
#   sides of a rect
# * the stuff lib is pretty good IMHO, maybe it belongs in it's own project?

# 2022-04-25
# * added option to load rects from subdividerect.py generated pickle

# 2022-03-20
# * added middle-click camera movement.
#
# * This project is shaping up and I would hate to lost any comments I made. So
#   Below is any old comments I happen to find that would normally be removed.
#   This comment, (2022-03-20), servs to remind me to add comments I want to
#   keep, here.

# 2022-01-28
# Ok, the update function now works in a fairly general fashion, for any of
# the four sides.
