import code
import pickle

from operator import attrgetter
from types import SimpleNamespace

import rectop

from lib.external import pygame
from lib.rectutil import rect_from_points

from .operation import FillOperation

dispatch = {}

modes = ['cutpos', 'cut', 'fill', 'defrag']

ns = SimpleNamespace(
    frames_per_second = 60,
    elapsed = None,
    screen = None,
    clock = None,
    field = None, # initial rect to cut up
    rects = None,
    rectcolors = {},
    rectcolors2 = {},
    drag = None,
    mode = modes[0],
    fill = None,
    fill_rects = [],
)

def on_event(event):
    """
    Dispatch to more specific event handler.
    """
    if event.type in dispatch:
        dispatch[event.type](event)

def on_keydown(event):
    if event.key in (pygame.K_ESCAPE, pygame.K_q):
        pygame.event.post(pygame.event.Event(pygame.QUIT))
    elif event.key == pygame.K_c:
        if ns.mode == 'cut':
            ns.mode = 'cutpos'
        else:
            ns.mode = 'cut'
    elif event.key == pygame.K_f:
        ns.mode = 'fill'
    elif event.key == pygame.K_d:
        ns.mode = 'defrag'
    elif event.key == pygame.K_BACKQUOTE:
        code.interact(local=globals())

def get_worldpos(screen_pos):
    return (
        screen_pos[0] - ns.camera.x,
        screen_pos[1] - ns.camera.y,
    )

def do_fill(worldpos):
    if not ns.fill:
        ns.fill = FillOperation(worldpos)

def on_mousebuttondown(event):
    if event.button == 2:
        # move camera
        ns.move_camera = True
    if ns.mode in ('cut', 'cutpos', 'defrag'):
        if event.button == pygame.BUTTON_LEFT:
            # start drag
            ns.drag = get_worldpos(event.pos)
    elif ns.mode == 'fill' and event.button == 1:
        do_fill(get_worldpos(event.pos))

def on_mousebuttonup(event):
    if ns.move_camera and event.button == 2:
        ns.move_camera = False
    if ns.mode in ('cut', 'cutpos', 'defrag'):
        if ns.drag and event.button in (1,3):
            if event.button == 1:
                # end drag and cut or defrag
                wpos = get_worldpos(event.pos)
                if ns.mode == 'cut':
                    knife = rect_from_points([ns.drag, wpos])
                elif ns.mode == 'cutpos':
                    knife = wpos
                elif ns.mode == 'defrag':
                    defrag_rect = rect_from_points([ns.drag, wpos])

                if ns.mode == 'defrag':
                    colliding = [rect for rect in ns.rects if defrag_rect.colliderect(rect)]
                    ops = rectop.join.defrag(colliding)
                    rectop.join.apply(ops, ns.rects)

                elif ns.rects and ns.mode in ('cut', 'cutpos'):
                    if ns.mode == 'cut':
                        cutter = rectop.cut.rect
                    elif ns.mode == 'cutpos':
                        cutter = rectop.cut.position
                    subdivide_all(knife, ns.rects, cutter)
            ns.drag = None

def on_mousemotion(event):
    if ns.move_camera:
        ns.camera.move_ip(*event.rel)

def subdivide_all(knife, rects, cutter):
    """
    Apply cutting operation to rects.
    """
    if isinstance(knife, pygame.Rect):
        predicate = lambda rect: rect.colliderect(knife)
    else:
        # assume position
        predicate = lambda rect: rect.collidepoint(knife)

    colliding = [rect for rect in rects if predicate(rect)]

    newrects = []
    for rect in colliding:
        rects.remove(rect)
        subrects = cutter(knife, rect)
        if subrects:
            newrects.extend(subrects)
            rects.extend(subrects)

    # defrag joins the point-cut rects back together
    if ns.mode != 'cutpos':
        ops = rectop.join.defrag(newrects)
        rectop.join.apply(ops, rects)

def draw():
    ns.screen.fill((0,0,0))
    pygame.draw.rect(ns.screen, (100,)*3, ns.field.move(*ns.camera.topleft), 1)
    mousepos = get_worldpos(pygame.mouse.get_pos())
    status = [f'{len(ns.rects)!r}']
    for rect in ns.rects + ns.fill_rects:
        if rect in ns.fill_rects:
            color = (200,10,200)
        else:
            trect = tuple(rect)
            if trect in ns.rectcolors2:
                color = ns.rectcolors2[trect]
            else:
                if trect not in ns.rectcolors:
                    ns.rectcolors[trect] = (200,)*3
                color = ns.rectcolors[trect]
        if not ns.drag and rect.collidepoint(mousepos):
            status.append(f'rect: {rect}')
            width = 4
        else:
            width = 1
        pygame.draw.rect(ns.screen, color, rect.move(*ns.camera.topleft), width)

    if ns.drag:
        rect = rect_from_points([ns.drag, mousepos])
        pygame.draw.rect(ns.screen, (10,200,10), rect.move(*ns.camera.topleft), 1)

    font = pygame.font.Font(None, 24)
    image = font.render(ns.mode, True, (200,20,20))
    ns.screen.blit(image, image.get_rect(topright=ns.frame.inflate(-10,-10).topright))

    image = font.render(f'world: {mousepos}', True, (200,)*3)
    rect = image.get_rect(bottomright=ns.frame.bottomright)
    ns.screen.blit(image, rect)

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
        update()
        draw()

def update():
    if ns.fill:
        ns.fill.update(ns)
        if ns.fill.is_done:
            ns.fill = None

def reset():
    ns.rects = [ns.field.inflate(-200, -200)]

def init_parser(parser):
    """
    """
    parser.add_argument('--rects', help='Load rects from pickle.')
    parser.set_defaults(func=run)

def run(args):
    """
    Place rects covering all empty space.
    """
    pygame.font.init()
    ns.screen = pygame.display.set_mode((1024, 900))
    ns.frame = ns.screen.get_rect()
    ns.clock = pygame.time.Clock()
    ns.camera = ns.frame.copy()
    ns.move_camera = False

    dispatch[pygame.KEYDOWN] = on_keydown
    dispatch[pygame.MOUSEBUTTONDOWN] = on_mousebuttondown
    dispatch[pygame.MOUSEBUTTONUP] = on_mousebuttonup
    dispatch[pygame.MOUSEMOTION] = on_mousemotion

    ns.field = ns.frame.copy()

    # 630,630

    if args.rects:
        with open(args.rects, 'rb') as fp:
            ns.rects = [pygame.Rect(*tup) for tup in pickle.load(fp)]
    else:
        reset()

    loop()
