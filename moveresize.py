import argparse
import random

from lib.external import pygame
from lib.rectutil import rect_wrap

FPS = 60
SCREEN = pygame.Rect(0,0,800,800)

UGLYKEYS = ('white', 'black', 'grey', 'gray')

COLORFUL = list(
    pygame.color.THECOLORS[key]
    for key in pygame.color.THECOLORS
    if not any(ugly in key for ugly in UGLYKEYS)
)

def squeeze_height(rect, y):
    rect.top += y
    rect.height -= y

class EditRect:

    def __init__(self, *rectargs):
        self.rect = pygame.Rect(*rectargs)
        size = min(self.rect.size) // 4
        if size < 25:
            size = 25
        self.init_handles(size)

    def init_handles(self, size):
        # handles
        rect = self.rect
        self.top = pygame.Rect(rect.left, rect.top - size, rect.width, size)
        self.topright = pygame.Rect(rect.right, rect.top - size, size, size)
        self.right = pygame.Rect(rect.right, rect.top, size, rect.height)
        self.bottomright = pygame.Rect(rect.right, rect.bottom, size, size)
        self.bottom = pygame.Rect(rect.left, rect.bottom, rect.width, size)
        self.bottomleft = pygame.Rect(rect.left - size, rect.bottom, size, size)
        self.left = pygame.Rect(rect.left - size, rect.top, size, rect.height)
        self.topleft = pygame.Rect(rect.left - size, rect.top - size, size, size)

    def handles(self):
        return iter((self.top, self.topright, self.right, self.bottomright,
            self.bottom, self.bottomleft, self.left, self.topleft))

    def drag(self, handle, *pos):
        try:
            x, y = pos
        except ValueError:
            x, y = pos[0]
        if handle in (self.top, self.bottom):
            x = 0
        elif handle in (self.left, self.right):
            y = 0
        handle.move_ip(x, y)
        #
        if handle is self.top:
            squeeze_height(self.rect, y)
            squeeze_height(self.left, y)
            squeeze_height(self.right, y)
        elif handle is self.bottom:
            self.rect.height -= abs(y)

        if handle is self.top:
            self.topleft.bottom = self.topright.bottom = self.rect.top
        elif handle is self.bottom:
            self.bottomleft.top = self.bottomright.top = self.bottom.top = self.rect.bottom
            squeeze_height(self.left, abs(y))
            squeeze_height(self.right, abs(y))
            self.left.bottom = self.right.bottom = self.rect.bottom

    def update_handles(self):
        self.top.bottomleft = self.rect.topleft
        self.topright.bottomleft = self.rect.topright
        self.right.topleft = self.rect.topright
        self.bottomright.topleft = self.rect.bottomright
        self.bottom.topleft = self.rect.bottomleft
        self.bottomleft.topright = self.rect.bottomleft
        self.left.topright = self.rect.topleft
        self.topleft.bottomright = self.rect.topleft


def main(argv=None):
    """
    Move and resize rects.
    """
    parser = argparse.ArgumentParser(description=main.__doc__)
    args = parser.parse_args(argv)

    screen = pygame.display.set_mode(SCREEN.size)
    frame = screen.get_rect()
    clock = pygame.time.Clock()

    # simple moveable and resizeable rect to see what kinds of things are needed.

    rect = EditRect(frame.inflate(-frame.width//2, -frame.height//2))
    color = (200,)*3
    show_handles = False
    handle = None
    drag = None

    handles = list(id(r) for r in rect.handles())
    colors = random.sample(COLORFUL, len(handles))
    colors = dict(zip(handles, colors))

    running = True
    while running:
        elapsed = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
            elif event.type == pygame.MOUSEMOTION:
                if drag:
                    rect.drag(drag, event.rel)
                else:
                    show_handles = rect.rect.collidepoint(event.pos)
                    if not show_handles:
                        query = (r for r in rect.handles() if r.collidepoint(event.pos))
                        handle = next(query, None)
                        show_handles = bool(handle)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT and handle:
                    drag = handle
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == pygame.BUTTON_LEFT:
                    drag = None

        screen.fill((0,)*3)
        # handles
        if show_handles:
            for r in rect.handles():
                if r is handle:
                    c = (200,200,100)
                else:
                    c = colors[id(r)]
                pygame.draw.rect(screen, c, r, 1)

        # main, editing rect
        pygame.draw.rect(screen, color, rect, 1)
        pygame.display.flip()

if __name__ == '__main__':
    main()
