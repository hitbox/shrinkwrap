import argparse

from types import SimpleNamespace

from lib.external import pygame
from lib.rectside import RectSide
from lib.rectutil import rect_from_points
from lib.rectutil import rect_get
from lib.rectutil import rect_get_barriers

ns = SimpleNamespace(
    frames_per_second = 60,
    elapsed = None,
    screen = None,
    clock = None,

    field = None, # rect to place random rects in
    obstructions = None,
    emptyspace = None,
)

def side2rect(rect, side):
    if side not in ('top', 'right', 'bottom', 'left'):
        raise ValueError

    if side in ('top', 'bottom'):
        x1, x2 = rect.left, rect.right
        y1 = y2 = getattr(rect, side)
    elif side in ('left', 'right'):
        x1 = x2 = getattr(rect, side)
        y1, y2 = rect.top, right.bottom

    rect = rect_from_points((x1,y1),(x2,y2))

def side_projection(rect, side, obstructions):
    siderect = side2rect(rect, side)

def recursive_find_empty(rect, obstructions):
    pass

def on_event(event):
    if event.type == pygame.KEYDOWN:
        on_keydown(event)

def on_keydown(event):
    if event.key in (pygame.K_ESCAPE, pygame.K_q):
        pygame.event.post(pygame.event.Event(pygame.QUIT))

def update():
    if ns.obstructions:
        walls = rect_get_barriers(ns.field)
        obstructions
        ns.emptyspace = recursive_find_empty(ns.obstructions[0])
    else:
        ns.emptyspace = None

def draw():
    ns.screen.fill((0,0,0))

    for rect in ns.obstructions:
        pygame.draw.rect(ns.screen, (200,)*3, rect, 1)

    pygame.draw.rect(ns.screen, (100,)*3, ns.field, 1)
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

def main(argv=None):
    """
    Place rects covering all empty space.
    """
    parser = argparse.ArgumentParser(description=main.__doc__)
    args = parser.parse_args(argv)

    ns.screen = pygame.display.set_mode((800, 600))
    ns.frame = ns.screen.get_rect()
    ns.clock = pygame.time.Clock()

    ns.field = ns.frame.inflate(-ns.frame.width//2, -ns.frame.height//2)
    ns.obstructions = [
        rect_get(ns.frame, size=(50,50), center=ns.field.center),
        rect_get(ns.frame, size=(25,25), top=ns.field.top + 10, centerx=ns.frame.centerx),
    ]

    loop()

if __name__ == '__main__':
    main()
