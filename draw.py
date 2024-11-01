import pygame
from pygame import gfxdraw


def draw_circle(
    window: pygame.Surface,
    x: float,
    y: float,
    radius: float,
    color: tuple,
    filled: bool = True,
):
    _x = int(x)
    _y = int(y)
    _radius = int(radius)
    gfxdraw.aacircle(window, _x, _y, _radius, color)
    if filled:
        gfxdraw.filled_circle(window, _x, _y, _radius, color)


def draw_line(
    window: pygame.Surface, x1: float, y1: float, x2: float, y2: float, color: tuple
):
    _x1 = int(x1)
    _y1 = int(y1)
    _x2 = int(x2)
    _y2 = int(y2)
    try:
        gfxdraw.line(window, _x1, _y1, _x2, _y2, color)
    except OverflowError:
        pass
