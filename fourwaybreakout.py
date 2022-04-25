import argparse
import random

from lib.external import pygame

FPS = 60
SCREEN = pygame.Rect(0,0,800,800)
BLOCK = pygame.Rect(0,0,SCREEN.width//16,SCREEN.height//16)

def main(argv=None):
    """
    bounce a rect around making a dungeon
    """
    parser = argparse.ArgumentParser(description=main.__doc__)
    args = parser.parse_args(argv)

    screen = pygame.display.set_mode(SCREEN.size)
    frame = screen.get_rect()
    clock = pygame.time.Clock()
    frames_per_second = 60
    highlight = None

    render = pygame.sprite.Group()
    walls = pygame.sprite.Group()

    wall_image = pygame.Surface(BLOCK.size)
    wall_image.fill((30,)*3)
    pygame.draw.rect(wall_image, (200,)*3, wall_image.get_rect(), 1)

    bounce = pygame.sprite.Sprite(render)
    bounce.rect = pygame.Rect((0,0),BLOCK.inflate(-BLOCK.width*.75,-BLOCK.height*.75).size)
    bounce.image = pygame.Surface(bounce.rect.size)
    bounce.image.fill((200,30,30))

    for y in range(frame.top, frame.bottom, BLOCK.height):
        for x in range(frame.left, frame.right, BLOCK.width):
            rect = pygame.Rect((x,y),BLOCK.size)
            if not rect.collidepoint(frame.center):
                wall_sprite = pygame.sprite.Sprite(walls, render)
                wall_sprite.image = wall_image
                wall_sprite.rect = rect
            else:
                # empty space to place the bouncing rect
                bounce.x = rect.centerx
                bounce.y = rect.centery
                bounce.dx = 2 * random.random()
                bounce.dy = 2 * random.random()

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
                for wall in walls:
                    if wall.rect.collidepoint(event.pos):
                        highlight = wall
                        break
                else:
                    highlight = None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if highlight:
                    walls.remove(highlight)
                    highlight = None

        for attr in 'xy':
            setattr(bounce, attr, getattr(bounce, attr) + getattr(bounce, 'd'+attr))
            setattr(bounce.rect, attr, getattr(bounce, attr))
            for wall in walls:
                if bounce.rect.colliderect(wall):
                    walls.remove(wall)
                    setattr(bounce, 'd'+attr, getattr(bounce, 'd'+attr) * -1)
                    break
            else:
                # we did not break for the other attribute, check the next one
                continue
            # did break so already collided, do not check other
            break

        screen.fill((0,)*3)
        render.draw(screen)
        pygame.display.flip()

if __name__ == '__main__':
    main()

