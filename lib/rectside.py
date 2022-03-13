import enum
import operator
import unittest

from .external import pygame

class RectSide(enum.Enum):
    # around the rect order, starting from top

    # NOTE:
    #   Was thinking this is too clever--methods in your Enum. The only example
    #   of the standard library doing this:
    #       * cpython/Lib/ast.py
    #   And only one method, `next`, like this one has.

    top = enum.auto()
    right = enum.auto()
    bottom = enum.auto()
    left = enum.auto()

    def next(self, delta=1):
        """
        Return the next side with wraparound.
        """
        sides = list(self.__class__)
        index = (sides.index(self) + delta) % len(sides)
        return sides[index]

    def adjacents(self):
        """
        Return the two adjacent sides.
        """
        return (self.next(-1), self.next(1))

    def opposite(self):
        return self.next(2)

    def side_value(self, rect):
        """
        Return the scalar value of the side of `rect`.
        """
        return getattr(rect, self.name)

    def side_rect(self, rect):
        """
        Return a pygame.Rect of side `self` of `rect`.
        """
        # TODO: tests
        # FIXME: remove dependency on pygame
        adjacents = self.adjacents()
        adjacent1, adjacent2 = adjacents
        min_adjacent = min(adjacent.side_value(rect) for adjacent in adjacents)
        # use the normal like a mask
        topleft = tuple(
            self.side_value(rect) if normval != 0 else min_adjacent
            for normval in self.normal
        )
        width_or_height = abs(adjacent1.side_value(rect) - adjacent2.side_value(rect))
        size = tuple(
            width_or_height if normval == 0 else 0
            for normval in self.normal
        )
        return pygame.Rect(topleft, size)


RectSide.top.normal = (0, -1)
RectSide.right.normal = (1, 0)
RectSide.bottom.normal = (0, 1)
RectSide.left.normal = (-1, 0)

getsides = operator.attrgetter(*RectSide.__members__)

class TestRectSide(unittest.TestCase):

    def test_rectside_next(self):
        self.assertEqual(RectSide.top.next(), RectSide.right)
        self.assertEqual(RectSide.right.next(), RectSide.bottom)
        self.assertEqual(RectSide.bottom.next(), RectSide.left)
        self.assertEqual(RectSide.left.next(), RectSide.top)

    def test_rectside_opposite(self):
        self.assertEqual(RectSide.top.opposite(), RectSide.bottom)
        self.assertEqual(RectSide.right.opposite(), RectSide.left)
        self.assertEqual(RectSide.bottom.opposite(), RectSide.top)
        self.assertEqual(RectSide.left.opposite(), RectSide.right)

    def test_rectside_adjacents(self):
        self.assertEqual(RectSide.top.adjacents(), (RectSide.left, RectSide.right))
        self.assertEqual(RectSide.right.adjacents(), (RectSide.top, RectSide.bottom))
        self.assertEqual(RectSide.bottom.adjacents(), (RectSide.right, RectSide.left))
        self.assertEqual(RectSide.left.adjacents(), (RectSide.bottom, RectSide.top))

    def test_rectside_rect_value(self):
        self.assertEqual(RectSide.top.side_value(pygame.Rect(0, 10, 5, 5)), 10)

    def test_getsides(self):
        # top, right, bottom, left
        sides = getsides(pygame.Rect(5,10,20,40))
        self.assertEqual(sides, (10,25,50,5))


if __name__ == '__main__':
    unittest.main()
