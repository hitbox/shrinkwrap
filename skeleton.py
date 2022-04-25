import argparse

from lib.external import pygame

FPS = 60
SCREEN = pygame.Rect(0,0,800,800)

def main(argv=None):
    """
    """
    parser = argparse.ArgumentParser(description=main.__doc__)
    args = parser.parse_args(argv)

    screen = pygame.display.set_mode(SCREEN.size)
    frame = screen.get_rect()
    clock = pygame.time.Clock()

    running = True
    while running:
        elapsed = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.event.post(pygame.event.Event(pygame.QUIT))

        screen.fill((0,)*3)
        pygame.display.flip()

if __name__ == '__main__':
    main()
