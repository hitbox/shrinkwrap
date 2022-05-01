from abc import ABC
from abc import abstractmethod
from operator import attrgetter

from lib.external import pygame
import rectop

# About this ABC business. Want a specification that `is_done` must be
# implemented but also it is so simple and common it should just be there.
# Doesn't this also mean that at some point (__init__ probably) is_done must be
# set, before it is checked by the loop?

class OperationABC(ABC):

    @abstractmethod
    def update(self, namespace):
        """
        """

    @property
    @abstractmethod
    def is_done(self):
        """
        """

    @is_done.setter
    @abstractmethod
    def is_done(self, value):
        """
        """


class BaseOperation(OperationABC):

    @property
    def is_done(self):
        return self._is_done

    @is_done.setter
    def is_done(self, value):
        self._is_done = value


class FillOperation(BaseOperation):

    def __init__(self, start):
        self.fx, self.fy = start
        self.step = 1
        self.wait = 0
        self.delay = 500

        self.above = None
        self.lowest_above = None
        self.top = None

        self.rightof = None
        self.leftmost_rightof = None
        self.right = None

        self.leftof = None
        self.rightmost_leftof = None
        self.left = None

        self.below = None
        self.topmost_below = None
        self.bottom = None

        # see above, at top.
        self.is_done = False

    def current_step(self):
        return getattr(self, f'step{self.step}')

    def update(self, namespace):
        if self.wait == 0:
            namespace.rectcolors2 = {}
            if not self.step:
                self.is_done = True
                return
            step_func = self.current_step()
            step_func(namespace)
        else:
            self.wait -= namespace.elapsed
            if self.wait < 0:
                self.wait = 0

    def step1(self, namespace):
        # check empty space
        for rect in namespace.rects:
            if rect.collidepoint((self.fx, self.fy)):
                # inside a rect, cancel fill
                namespace.rectcolors2[tuple(rect)] = (200,10,10)
                self.step = 0
                break
        else:
            # not inside any rects, go to next step
            self.step += 1
            self.wait = 0

    def step2(self, namespace):
        # find rects above
        self.above = rectop.query.filter_rects(
            namespace.rects, 'top', pygame.Rect(self.fx, self.fy, 1, 1))
        self.above = list(self.above)
        for rect in self.above:
            namespace.rectcolors2[tuple(rect)] = (200,10,10)
        self.wait = self.delay
        self.step += 1

    def step3(self, namespace):
        # nearest above
        self.above = sorted(self.above, key=attrgetter('bottom'))
        if self.above:
            self.lowest_above = self.above[-1]
            self.top = self.lowest_above.bottom
            namespace.rectcolors2[tuple(self.lowest_above)] = (200,10,10)
            self.step += 1
            self.wait = self.delay

    def step4(self, namespace):
        # find rects to the right of
        self.rightof = rectop.query.filter_rects(
            namespace.rects, 'right', pygame.Rect(self.fx, self.fy, 1, 1))
        self.rightof = list(self.rightof)
        for rect in self.rightof:
            namespace.rectcolors2[tuple(rect)] = (200,10,10)
        self.wait = self.delay
        self.step += 1

    def step5(self, namespace):
        self.rightof = sorted(self.rightof, key=attrgetter('left'))
        if self.rightof:
            self.leftmost_rightof = self.rightof[0]
            self.right = self.leftmost_rightof.left
            namespace.rectcolors2[tuple(self.leftmost_rightof)] = (200,10,10)
            self.step += 1
            self.wait = self.delay

    def step6(self, namespace):
        # left of
        self.leftof = rectop.query.filter_rects(
            namespace.rects, 'left', pygame.Rect(self.fx, self.fy, 1, 1))
        self.leftof = list(self.leftof)
        for rect in self.leftof:
            namespace.rectcolors2[tuple(rect)] = (200,10,10)
        self.wait = self.delay
        self.step += 1

    def step7(self, namespace):
        # left
        self.leftof = sorted(self.leftof, key=attrgetter('right'))
        if self.leftof:
            self.rightmost_leftof = self.leftof[-1]
            self.left = self.rightmost_leftof.right
            namespace.rectcolors2[tuple(self.rightmost_leftof)] = (200,10,10)
            self.step += 1
            self.wait = self.delay

    def step8(self, namespace):
        # below
        self.below = rectop.query.filter_rects(
            namespace.rects, 'bottom', pygame.Rect(self.fx, self.fy, 1, 1))
        self.below = list(self.below)
        for rect in self.below:
            namespace.rectcolors2[tuple(rect)] = (200,10,10)
        self.wait = self.delay
        self.step += 1

    def step9(self, namespace):
        self.below = sorted(self.below, key=attrgetter('top'))
        if self.below:
            self.topmost_below = self.below[0]
            self.bottom = self.topmost_below.top
            namespace.rectcolors2[tuple(self.topmost_below)] = (200,10,10)
            self.step += 1
            self.wait = self.delay

    def step10(self, namespace):
        # construct fill rect
        width = self.right - self.left
        height = self.bottom - self.top
        r = pygame.Rect(self.left, self.top, width, height)
        namespace.fill_rects.append(r)
        self.wait = self.delay
        self.step = 0
