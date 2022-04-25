import argparse
import code
import enum
import pickle
import random

from itertools import cycle
from types import SimpleNamespace

from lib import rectop
from lib.external import pygame
from lib.rectside import RectSide
from lib.rectutil import rect_from_points
from lib.rectutil import rect_get
from lib.rectutil import rect_get_barriers
from lib.rectutil import rect_wrap

class JoinType(enum.Enum):
    SAME = enum.auto()
    HORIZONTAL = enum.auto()
    VERTICAL = enum.auto()


ns = SimpleNamespace(
    frames_per_second = 60,
    elapsed = None,
    screen = None,
    clock = None,

    field = None, # rect to place random rects in
    rects = None,

    rectcolors = {},

    short = 0,

    #
    drag = None,
)

def on_event(event):
    if event.type in dispatch:
        dispatch[event.type](event)

def on_keydown(event):
    if event.key in (pygame.K_ESCAPE, pygame.K_q):
        pygame.event.post(pygame.event.Event(pygame.QUIT))
    elif event.key == pygame.K_r:
        reset(ns)
    elif event.key == pygame.K_BACKQUOTE:
        code.interact(local=globals())

def get_worldpos(screen_pos):
    return (
        screen_pos[0] - ns.camera.x,
        screen_pos[1] - ns.camera.y,
    )

def on_mousebuttondown(event):
    if event.button == 1:
        # start drag
        ns.drag = get_worldpos(event.pos)
    elif event.button == 2:
        # move camera
        ns.move_camera = True

def on_mousebuttonup(event):
    if ns.move_camera and event.button == 2:
        ns.move_camera = False
    if ns.drag:
        if event.button == 3:
            # abort cut
            pass
        elif event.button == 1:
            # end drag and cut
            kniferect = rect_from_points([ns.drag, get_worldpos(event.pos)])
            if ns.rects:
                subdivide_all(kniferect, ns.rects)
        ns.drag = None

def on_mousemotion(event):
    if ns.move_camera:
        ns.camera.move_ip(*event.rel)

def get_jointype(r1, r2):
    if tuple(r1) == tuple(r2):
        return JoinType.SAME
    elif r1.y == r2.y and r1.height == r2.height:
        if r1.right == r2.left or r2.right == r1.left:
            return JoinType.HORIZONTAL
    elif r1.x == r2.x and r1.width == r2.width:
        if r1.bottom == r2.top or r2.bottom == r1.top:
            return JoinType.VERTICAL

def get_joined(r1, r2, jointype):
    if jointype is JoinType.SAME:
        # either will do
        return r1.copy()
    else:
        return rect_wrap([r1, r2])

def area(rect):
    return rect.width * rect.height

def subdivide_all(kniferect, rects):
    colliding = [rect for rect in rects if kniferect.colliderect(rect)]
    for emptyrect in colliding:
        rects.remove(emptyrect)
        empties = rectop.cut(kniferect, emptyrect)
        rects.extend(empties)
    rectop.defrag(rects)

dispatch = {
    pygame.KEYDOWN: on_keydown,
    pygame.MOUSEBUTTONDOWN: on_mousebuttondown,
    pygame.MOUSEBUTTONUP: on_mousebuttonup,
    pygame.MOUSEMOTION: on_mousemotion,
}

def update():
    """
    """

def draw_shade(surf, color, rect, step=None, width=None):
    # XXX: why is shading like this so hard. this doesn't work!
    if step is None:
        step = 8
    if width is None:
        width = 1
    x, y = rect.topleft
    while x < rect.right or y < rect.bottom:
        pygame.draw.line(surf, color, (rect.left, y), (x, rect.top), width)
        if x < rect.right:
            x += step
        if y < rect.bottom:
            y += step

def draw():
    ns.screen.fill((0,0,0))

    pygame.draw.rect(ns.screen, (100,)*3, ns.field.move(*ns.camera.topleft), 1)

    mousepos = get_worldpos(pygame.mouse.get_pos())

    status = [f'{len(ns.rects)!r}']
    if ns.rects:
        for rect in ns.rects:
            if tuple(rect) not in ns.rectcolors:
                r = random.randint(75,200)
                g = random.randint(75,200)
                b = random.randint(75,200)
                r, g, b = (200,)*3
                ns.rectcolors[tuple(rect)] = (r,g,b)
            color = ns.rectcolors[tuple(rect)]
            if rect.collidepoint(mousepos):
                status.append(f'rect: {rect}')
                width = 4
            else:
                width = 1
            pygame.draw.rect(ns.screen, color, rect.move(*ns.camera.topleft), width)

    if ns.drag:
        rect = rect_from_points([ns.drag, mousepos])
        pygame.draw.rect(ns.screen, (10,200,10), rect.move(*ns.camera.topleft), 1)

    font = pygame.font.Font(None, 24)
    y = 10
    for msg in status:
        image = font.render(msg, True, (200,25,25))
        rect = image.get_rect(x = 10, y = y)
        ns.screen.blit(image, rect.move(*ns.camera.topleft))
        y += rect.height + 10

    pygame.display.flip()

def loop():
    running = True
    while running:
        ns.elapsed = ns.clock.tick(ns.frames_per_second)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                on_event(event)
        # update
        update()
        draw()

def reset():
    ns.rects = [ns.field.inflate(-200, -200)]

def main(argv=None):
    """
    Place rects covering all empty space.
    """
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('--rects', help='Load rects from pickle.')
    args = parser.parse_args(argv)

    pygame.font.init()
    ns.screen = pygame.display.set_mode((1024, 900))
    ns.frame = ns.screen.get_rect()
    ns.clock = pygame.time.Clock()
    ns.camera = ns.frame.copy()
    ns.move_camera = False

    ns.field = ns.frame.copy()

    if args.rects:
        with open(args.rects, 'rb') as fp:
            ns.rects = [pygame.Rect(*tup) for tup in pickle.load(fp)]
    else:
        reset()

    loop()

if __name__ == '__main__':
    main()
