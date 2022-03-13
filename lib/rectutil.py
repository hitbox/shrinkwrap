import enum
import unittest

from .external import pygame

class RectPoints(enum.Enum):
    midtop = enum.auto()
    topright = enum.auto()
    midright = enum.auto()
    bottomright = enum.auto()
    midbottom = enum.auto()
    bottomleft = enum.auto()
    midleft = enum.auto()
    topleft = enum.auto()


def iterpoints(rect):
    """
    Iterate important points, clockwise, around a rect; starting at midtop.
    """
    return (getattr(rect, point.name) for point in RectPoints)

def rect_from_points(points):
    """
    """
    xs, ys = zip(*points)
    left, right = min(xs), max(xs)
    top, bottom = min(ys), max(ys)
    width = right - left
    height = bottom - top
    return pygame.Rect(left, top, width, height)

class TestCase(unittest.TestCase):

    def setUp(self):
        self.rect = pygame.Rect(10,15,30,25)

    def test_iterpoints(self):
        a = list(iterpoints(self.rect))
        b = [
            (10+15, 15), # midtop
            (10+30, 15), # topright
            (10+30, 15+25//2), # midright
            (10+30, 15+25), # bottomright
            (10+15, 15+25), # midbottom
            (10, 15+25), # bottomleft
            (10, 15+25//2), # midleft
            (10, 15), # topleft
        ]
        self.assertEqual(a, b)

    def test_rect_from_points(self):
        points = [(10,15),(40,15+25)]
        rect = rect_from_points(points)
        self.assertEqual(rect, self.rect)


if __name__ == '__main__':
    unittest.main()
