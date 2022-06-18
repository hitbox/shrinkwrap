import argparse
import random
import time

from itertools import combinations

import rectop

from lib.external import pygame

DEBUGCOLOR = (200,30,200)
BGCOLOR = (0,)*3
BGCOLOR2 = (10,)*3

FGCOLOR = (200,)*3
FGCOLOR2 = (230,)*3

CURVE_CONNECTIONS = {
    ('midtop', 'midright'): 'topright',
    ('midright', 'midbottom'): 'bottomright',
    ('midbottom', 'midleft'): 'bottomleft',
    ('midleft', 'midtop'): 'topleft',
}

def render_truchet_tile(
    midpoints_radius,
    corners_radius,
    connections,
):
    """
    Render truchet tile.
    :param connections: 2-tuples of midpoint names to connect.
    """
    frame_bg_color = (30,) * 3
    tile_bg_color = (60,) * 3
    midpoint_color = (20,) * 3

    # NOTES
    # * maybe the little dots should not be "connectors" they should be "terminators".
    # * transparent "outside the tile" so that the overlapping works.

    small_diameter = midpoints_radius * 2
    big_diameter = corners_radius * 2

    frame_side_length = big_diameter * 2 + small_diameter
    frame_rect = pygame.Rect((0, )*2, (frame_side_length,)*2)

    surf = pygame.Surface(frame_rect.size)
    surf.fill(frame_bg_color)

    sidelen = big_diameter + small_diameter
    tile_rect = rectop.get.new(
        size = (sidelen, ) * 2,
        center = frame_rect.center,
    )

    pygame.draw.rect(surf, tile_bg_color, tile_rect)

    # draw curved and straight connections
    curve_radius = tile_rect.width // 2 + midpoints_radius

    dots = []
    connrects = []
    curves = []
    for attrs in connections:
        attr1, attr2 = attrs
        if attr1 is None:
            dots.append(attr2)
        elif attr2 is None:
            dots.append(attr1)
        elif rectop.get.opposite_midpoint(attr1) == attr2:
            # draw rect
            point1 = getattr(tile_rect, attr1)
            point2 = getattr(tile_rect, attr2)
            # sort top-bottom, left-right
            point1, point2 = sorted([point1, point2], key=lambda p: (p[1], p[0]))

            if (
                ('top' in attr1 or 'bottom' in attr1)
                and
                ('top' in attr2 or 'bottom' in attr2)
            ):
                # top-bottom
                x = tile_rect.centerx - midpoints_radius
                y = tile_rect.top
                width = small_diameter
                height = tile_rect.height
            else:
                # left-right
                x = tile_rect.left
                y = tile_rect.centery - midpoints_radius
                height = small_diameter
                width = tile_rect.width

            connrect = pygame.Rect(x,y,width,height)
            connrects.append((midpoint_color, connrect, 0))
        else:
            # curve
            for ATTRS, pointattr in CURVE_CONNECTIONS.items():
                if set(ATTRS) == set(attrs):
                    break
            else:
                raise ValueError
            point = getattr(tile_rect, pointattr)
            curves.append((midpoint_color, point, curve_radius, 0))
            curves.append((tile_bg_color, point, corners_radius, 0))

    # draw "curves"
    for color, center, radius, width in curves:
        pygame.draw.circle(surf, color, center, radius, width)

    # "clear" the big curve circles from the outside of the tile
    # NOTE: maybe do this with a separate surface, letting clipping do the work?
    for outside_rect in rectop.cut.with_knife(tile_rect, frame_rect):
        pygame.draw.rect(surf, frame_bg_color, outside_rect, 0)

    # draw straight horizontal and vertical connectors
    for color, rect, width in connrects:
        pygame.draw.rect(surf, color, rect, width)

    # draw little "connector" circles in midpoints
    for attr in dots:
        point = getattr(tile_rect, attr)
        pygame.draw.circle(surf, midpoint_color, point, midpoints_radius, 0)

    # draw the tile frame
    pygame.draw.rect(surf, DEBUGCOLOR, tile_rect, 1)

    return surf

def main(argv=None):
    """
    """
    parser = argparse.ArgumentParser()
    args = parser.parse_args(argv)

    pygame.font.init()

    window = pygame.display.set_mode((6*120,)*2)
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
    def next_truchet_image():
        """
        Generate the truchet image from connectors.
        """
        nonlocal truchet_image
        truchet_image = render_truchet_tile(
            midpoints_radius = min(frame.size) // (6*2),
            corners_radius = min(frame.size) // (6*1),
            connections = connections
        )

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
        # draw
        window.fill(BGCOLOR)
        # draw - truchet tile image
        window.blit(truchet_image, truchet_image.get_rect(center=frame.center))
        # draw - connector names
        connections_string = [f'{left} -> {right}' for left, right in connections]
        y = gui_frame.top
        for string in connections_string:
            image = font.render(string, True, FGCOLOR)
            rect = image.get_rect(right=gui_frame.right, y=y)
            window.blit(image, rect)
            y = rect.bottom
        # draw - FPS
        fps_image = font.render(f'{clock.get_fps():.2f}', True, FGCOLOR)
        window.blit(fps_image, fps_image.get_rect(bottomright=gui_frame.bottomright))
        # draw - crosshairs at mouse
        mx, my = pygame.mouse.get_pos()
        pygame.draw.line(window, DEBUGCOLOR, (frame.left, my), (frame.right, my))
        pygame.draw.line(window, DEBUGCOLOR, (mx, frame.top), (mx, frame.bottom))
        # draw - update
        pygame.display.flip()

#https://christophercarlson.com/portfolio/multi-scale-truchet-patterns/

if __name__ == '__main__':
    main()
