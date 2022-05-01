import pickle

from types import SimpleNamespace
from itertools import cycle

import rectop

from lib.external import pygame

DIRECTIONS = ['top', 'right', 'bottom', 'left']
DIRCYCLE = cycle(DIRECTIONS)

def dispatch(event):
    if event.type == pygame.KEYDOWN:
        on_keydown(event)
    elif event.type == pygame.MOUSEBUTTONDOWN:
        on_mousebuttondown(event)
    elif event.type == pygame.MOUSEMOTION:
        on_mousemotion(event)
    elif event.type == pygame.MOUSEBUTTONUP:
        on_mousebuttonup(event)

def on_keydown(event):
    if event.key in (pygame.K_ESCAPE, pygame.K_q):
        pygame.event.post(pygame.event.Event(pygame.QUIT))
    elif event.key in (pygame.K_SPACE, ):
        ns.facing = next(DIRCYCLE)
        print(ns.facing)
        do_query()

def on_mousebuttondown(event):
    if event.button == pygame.BUTTON_MIDDLE:
        ns.drag_rect = ns.camera

def on_mousemotion(event):
    if ns.drag_rect:
        ns.drag_rect.move_ip(event.rel)
    do_query()

def on_mousebuttonup(event):
    if event.button == pygame.BUTTON_MIDDLE:
        ns.drag_rect = None

def do_query():
    rects = rectop.query.filter_rects(ns.rects, ns.facing, ns.player)
    ns.highlight = list(rects)

def getworldpos(screen_pos, camera_rect):
    sx, sy = screen_pos
    cx, cy = camera_rect.topleft
    return (sx - cx, sy - cy)

def update():
    mpos = pygame.mouse.get_pos()
    wpos = getworldpos(mpos, ns.camera)
    ns.player.center = wpos

def draw():
    ns.screen.fill((0,)*3)

    for rect in ns.rects:
        if ns.highlight and rect in ns.highlight:
            color = (200, 10, 10)
        else:
            color = (200,)*3
        pygame.draw.rect(ns.screen, color, rect.move(ns.camera.topleft), 1)

    if ns.player:
        pygame.draw.rect(ns.screen, (200,10,100), ns.player)

    pygame.display.flip()

def loop():
    running = True
    while running:
        ns.elaped = ns.clock.tick(ns.fps)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                dispatch(event)
        update()
        draw()

def init_parser(parser):
    """
    """
    parser.add_argument('--rects', help='Pickle of pygame.Rect argument tuples.')
    parser.set_defaults(func=run)

def run(args):
    """
    Quick simplification to figure out why my "rightof", "below", etc. queries
    are not behaving correctly.
    """
    if not args.rects:
        rects = []
    else:
        with open(args.rects, 'rb') as fp:
            rects = [pygame.Rect(*args) for args in pickle.load(fp)]

    if rects:
        frame = rectop.get.wrap(rects)
    else:
        frame = pygame.Rect(0,0,1024,1024)

    screen = pygame.display.set_mode(frame.size)
    camera = screen.get_rect()
    clock = pygame.time.Clock()
    fps = 60

    global ns
    ns = SimpleNamespace(
        screen = screen,
        frame = frame,
        camera = camera,
        clock = clock,
        fps = fps,
        rects = rects,
        player = pygame.Rect(0,0,50,50),
        highlight = None,
        facing = next(DIRCYCLE),
        drag_rect = None,
    )
    print(ns.facing)
    loop()
