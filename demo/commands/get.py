import argparse
import pickle

from lib.external import pygame

def world_pos(screen_pos, camera, scale):
    return (
        screen_pos[0] // scale + -camera.x,
        screen_pos[1] // scale + -camera.y
    )

def init_parser(parser):
    """
    """
    parser.add_argument('--rects', help='Load rects from pickle.')
    parser.set_defaults(func=run)

def run(args):
    """
    Demo get operations on rects.
    """
    RESOLUTION = (256, 224)
    SCALE = 4

    pygame.font.init()

    font = pygame.font.Font(None, 20)
    camera = pygame.Rect((0,0), RESOLUTION)

    if args.rects:
        with open(args.rects, 'rb') as fp:
            rects = [pygame.Rect(*tup) for tup in pickle.load(fp)]
    else:
        x = min(camera.size) // 3
        rects = [camera.inflate(-x,-x)]

    screen = pygame.Surface(camera.size)
    window = pygame.Rect(0,0,camera.width*SCALE,camera.height*SCALE)
    real_screen = pygame.display.set_mode(window.size)
    clock = pygame.time.Clock()
    fps = 60
    drag = None
    hover = None

    running = True
    while running:
        elapsed = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_RIGHT:
                    drag = camera
            elif event.type == pygame.MOUSEMOTION:
                if drag:
                    drag.move_ip(-event.rel[0], -event.rel[1])
                elif not any(event.buttons):
                    # get hover on mouse move
                    pass
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == pygame.BUTTON_RIGHT:
                    drag = None
        #
        mouse_screen_pos = pygame.mouse.get_pos()
        mouse_screen_pos = (mouse_screen_pos[0] // SCALE, mouse_screen_pos[1] // SCALE)
        mouse_world_pos = world_pos(mouse_screen_pos, camera, SCALE)
        for rect in rects:
            if rect.collidepoint(mouse_world_pos):
                hover = rect
        #
        screen.fill((0,)*3)
        for rect in rects:
            pygame.draw.rect(screen, (200,)*3, rect.move(-camera.x, -camera.y), 1)
        pygame.draw.circle(screen, (200,10,10), mouse_screen_pos, 10, 1)
        #image = font.render(f'')
        pygame.transform.scale(screen, window.size, real_screen)
        pygame.display.flip()
