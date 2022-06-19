import argparse
import random
import time

from itertools import combinations

import rectop
import render.truchet

from lib.external import pygame

DEBUGCOLOR = (200,30,200)
BGCOLOR = (0,)*3
BGCOLOR2 = (10,)*3

FGCOLOR = (200,)*3
FGCOLOR2 = (230,)*3

def render_text_lines(font, antialias, color, lines):
    """
    Render lines of text.
    """
    images = [font.render(line, antialias, color) for line in lines]
    rects = [image.get_rect() for image in images]
    for r1, r2 in zip(rects[:-1], rects[1:]):
        r2.top = r1.bottom
    width = max(rect.right for rect in rects)
    height = sum(rect.height for rect in rects)
    surf = pygame.Surface((width, height))
    for rect, image in zip(rects, images):
        surf.blit(image, rect)
    return surf

def main(argv=None):
    """
    """
    parser = argparse.ArgumentParser()
    args = parser.parse_args(argv)

    pygame.font.init()

    window = pygame.display.set_mode((6*155,)*2)
    frame = window.get_rect()
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    population = rectop.MIDPOINTS + [None]
    midpoint_combinations = list(combinations(population, 2))

    connections = None
    def next_connections():
        """
        Randomly generate a list of curve connections.
        """
        nonlocal connections
        k = random.randint(1, len(midpoint_combinations)//2)
        connections = random.sample(midpoint_combinations, k)

    truchet_image = None
    truchet_rect = None
    connections_image = None
    connections_rect = None
    def next_truchet_image():
        """
        Generate the truchet image from connectors.
        """
        nonlocal truchet_image
        nonlocal truchet_rect
        nonlocal connections_image
        nonlocal connections_rect
        truchet_image = render.truchet.tile(
            midpoints_radius = min(frame.size) // (6*2),
            corners_radius = min(frame.size) // (6*1),
            connections = connections
        )
        truchet_rect = truchet_image.get_rect(center=frame.center)
        #
        connections_strings = [f'{left} -> {right}' for left, right in connections]
        connections_image = render_text_lines(font, True, FGCOLOR, connections_strings)
        connections_rect = connections_image.get_rect(topright=gui_frame.topright)

    draw_crosshairs = True
    gui_frame = frame.inflate(-20,-20)
    next_connections()
    next_truchet_image()
    running = True
    while running:
        clock.tick()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Q to quit
                if event.key in (pygame.K_q,):
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                # spacebar to move to next
                elif event.key in (pygame.K_SPACE,):
                    next_connections()
                    next_truchet_image()
                # S to toggle crosshairs
                elif event.key in (pygame.K_s,):
                    draw_crosshairs = not draw_crosshairs
        # draw
        window.fill(BGCOLOR)
        # draw - truchet tile image
        window.blit(truchet_image, truchet_rect)
        # draw - connector names
        window.blit(connections_image, connections_rect)
        # draw - FPS
        fps_image = font.render(f'{clock.get_fps():.2f}', True, FGCOLOR)
        window.blit(fps_image, fps_image.get_rect(bottomright=gui_frame.bottomright))
        # draw - crosshairs at mouse
        if draw_crosshairs:
            mx, my = pygame.mouse.get_pos()
            pygame.draw.line(window, DEBUGCOLOR, (frame.left, my), (frame.right, my))
            pygame.draw.line(window, DEBUGCOLOR, (mx, frame.top), (mx, frame.bottom))
        # draw - update
        pygame.display.flip()

#https://christophercarlson.com/portfolio/multi-scale-truchet-patterns/

if __name__ == '__main__':
    main()
