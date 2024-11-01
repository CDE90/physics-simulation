from __future__ import annotations

import math

import numpy as np
import pygame

from object import CircleBody, PolarVector


class Trail:
    def __init__(
        self, circle: CircleBody, max_length: int = 100, color: tuple = (255, 255, 255)
    ):
        self.circle = circle
        self.trail_points: list[PolarVector] = []
        self.bind_to_circle()

        self._max_length = max_length
        self._color = color
        self._trail_surface = pygame.Surface((1200, 800), pygame.SRCALPHA)

    def update(self, _: CircleBody):
        self.trail_points.append(self.circle.position)
        if len(self.trail_points) > self._max_length:
            self.trail_points.pop(0)

    def bind_to_circle(self):
        self.circle.add_update_listener(self.update)

    def draw(self, window: pygame.Surface):
        # Clear the trail surface
        self._trail_surface.fill((0, 0, 0, 0))

        # Draw anti-aliased points using aalines
        if len(self.trail_points) >= 2:
            points = [(int(p.x), int(p.y)) for p in self.trail_points]
            pygame.draw.aalines(self._trail_surface, self._color, False, points)

        # Blend the trail surface onto the main window
        window.blit(self._trail_surface, (0, 0))


class SmoothTrail:
    def __init__(
        self,
        circle: CircleBody,
        max_length: int = 100,
        color: tuple[int, int, int] = (255, 255, 255),
        width: int = 2,
        fade: bool = True,
    ):
        self.circle = circle
        self.trail_points: list[tuple[float, float]] = []
        self.bind_to_circle()

        self._max_length = max_length
        self._base_color = color
        self._line_width = width
        self._fade = fade

        # Create surfaces for main trail and anti-aliasing
        self._trail_surface = pygame.Surface((1200, 800), pygame.SRCALPHA)
        self._aa_surface = pygame.Surface((1200, 800), pygame.SRCALPHA)

    def update(self, _: CircleBody):
        self.trail_points.append((self.circle.x, self.circle.y))
        if len(self.trail_points) > self._max_length:
            self.trail_points.pop(0)

    def bind_to_circle(self):
        self.circle.add_update_listener(self.update)

    def draw(self, window: pygame.Surface):
        if len(self.trail_points) < 2:
            return

        # Clear the surfaces
        self._trail_surface.fill((0, 0, 0, 0))
        self._aa_surface.fill((0, 0, 0, 0))

        if self._fade:
            points = np.array(self.trail_points)
            for i in range(1, len(points)):
                progress = i / len(points)
                alpha = int(255 * progress)
                color = (*self._base_color, alpha)

                # Draw anti-aliased line segment
                pygame.draw.aaline(
                    self._aa_surface,
                    color,
                    points[i - 1],
                    points[i],
                )

                # Draw the main line with width
                pygame.draw.line(
                    self._trail_surface,
                    color,
                    points[i - 1],
                    points[i],
                    self._line_width,
                )

                # Draw anti-aliased circle at each point
                pygame.draw.circle(
                    self._aa_surface,
                    color,
                    points[i],
                    self._line_width // 2,
                )
        else:
            if len(self.trail_points) >= 2:
                # Draw anti-aliased outline
                pygame.draw.aalines(
                    self._aa_surface,
                    (*self._base_color, 255),
                    False,
                    self.trail_points,
                )

                # Draw main line with width
                pygame.draw.lines(
                    self._trail_surface,
                    (*self._base_color, 255),
                    False,
                    self.trail_points,
                    self._line_width,
                )

        # Blend both surfaces onto the main window
        window.blit(self._trail_surface, (0, 0))
        window.blit(self._aa_surface, (0, 0))


class SmoothTrailWithGlow:
    def __init__(
        self,
        circle: CircleBody,
        max_length: int = 100,
        color: tuple[int, int, int] = (255, 255, 255),
        width: int = 2,
        glow_radius: int = 10,
    ):
        self.circle = circle
        self.trail_points: list[
            tuple[float, float, float, float]
        ] = []  # x, y, vel_x, vel_y
        self.bind_to_circle()

        self._max_length = max_length
        self._base_color = color
        self._line_width = width
        self._glow_radius = glow_radius

        # Create surfaces for different effects
        self._trail_surface = pygame.Surface((1200, 800), pygame.SRCALPHA)
        self._glow_surface = pygame.Surface((1200, 800), pygame.SRCALPHA)
        self._aa_surface = pygame.Surface((1200, 800), pygame.SRCALPHA)

    def update(self, _: CircleBody):
        # Store position and velocity components
        self.trail_points.append(
            (
                self.circle.x,
                self.circle.y,
                self.circle.velocity.x,
                self.circle.velocity.y,
            )
        )
        if len(self.trail_points) > self._max_length:
            self.trail_points.pop(0)

    def bind_to_circle(self):
        self.circle.add_update_listener(self.update)

    def _draw_perpendicular_glow(
        self,
        surface: pygame.Surface,
        p1: tuple[float, float, float, float],
        width: float,
        color: tuple[int, int, int],
        alpha: int,
    ):
        """Draw a glow line perpendicular to the velocity vector"""
        x, y, vel_x, vel_y = p1

        # Calculate the perpendicular vector to velocity
        if abs(vel_x) < 1e-6 and abs(vel_y) < 1e-6:
            # If velocity is zero, skip drawing
            return

        # Normalize velocity vector
        vel_mag = math.sqrt(vel_x * vel_x + vel_y * vel_y)
        norm_vel_x = vel_x / vel_mag
        norm_vel_y = vel_y / vel_mag

        # Get perpendicular vector (-y, x)
        perp_x = -norm_vel_y
        perp_y = norm_vel_x

        # Calculate endpoints of the glow line
        half_width = width / 2
        start_point = (x + perp_x * half_width, y + perp_y * half_width)
        end_point = (x - perp_x * half_width, y - perp_y * half_width)

        # Draw the glow line
        pygame.draw.line(
            surface,
            (*color, alpha),
            start_point,
            end_point,
            max(1, int(width / 8)),  # Thin line for smooth blending
        )

    def draw(self, window: pygame.Surface):
        if len(self.trail_points) < 2:
            return

        # Clear all surfaces
        self._trail_surface.fill((0, 0, 0, 0))
        self._glow_surface.fill((0, 0, 0, 0))
        self._aa_surface.fill((0, 0, 0, 0))

        # Draw the glow effect
        glow_width = self._line_width + self._glow_radius * 2

        for i, point in enumerate(self.trail_points):
            progress = i / len(self.trail_points)
            alpha = int(155 * progress)

            # Draw multiple perpendicular glow lines with different widths
            for w_mult in [1.0, 0.8, 0.6]:
                self._draw_perpendicular_glow(
                    self._glow_surface,
                    point,
                    glow_width * w_mult,
                    self._base_color,
                    alpha // 4,
                )

        # Blend all surfaces onto the main window in the correct order
        window.blit(self._glow_surface, (0, 0))
        window.blit(self._trail_surface, (0, 0))
        window.blit(self._aa_surface, (0, 0))
