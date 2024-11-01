from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

import pygame

from draw import draw_circle


class PolarVector:
    def __init__(self, magnitude: float, angle: Angle):
        self.magnitude = magnitude
        self.angle = angle

    @classmethod
    def from_cartesian(cls, x: float, y: float):
        magnitude = math.sqrt(x**2 + y**2)
        angle = Angle(math.atan2(y, x) * 180 / math.pi)
        return cls(magnitude, angle)

    @property
    def x(self):
        return self.magnitude * math.cos(self.angle.angle)

    @property
    def y(self):
        return self.magnitude * math.sin(self.angle.angle)

    def __add__(self, other: PolarVector) -> PolarVector:
        # Use the law of cosines to find the magnitude
        angle_diff = self.angle.angle - other.angle.angle
        new_magnitude = math.sqrt(
            self.magnitude**2
            + other.magnitude**2
            + 2 * self.magnitude * other.magnitude * math.cos(angle_diff)
        )

        # Use the law of sines to find the new angle
        if new_magnitude == 0:
            new_angle = self.angle  # Arbitrary choice when magnitude is 0
        else:
            # Calculate new angle using atan2 for proper quadrant handling
            new_x = self.x + other.x
            new_y = self.y + other.y
            new_angle = Angle(math.atan2(new_y, new_x) * 180 / math.pi)

        return PolarVector(new_magnitude, new_angle)

    def __sub__(self, other: PolarVector) -> PolarVector:
        # Subtract by adding the negative of the other vector
        return self + PolarVector(other.magnitude, other.angle + Angle(180))

    def __mul__(self, scalar: float) -> PolarVector:
        # Multiplication by scalar only affects magnitude
        return PolarVector(
            self.magnitude * abs(scalar),
            self.angle + Angle(180) if scalar < 0 else self.angle,
        )

    def __truediv__(self, scalar: float) -> PolarVector:
        if scalar == 0:
            raise ValueError("Division by zero")
        return self * (1.0 / scalar)

    def rotate(self, angle: Angle) -> PolarVector:
        """Rotate the vector by the given angle."""
        return PolarVector(self.magnitude, self.angle + angle)

    def __repr__(self):
        return f"PolarVector({self.magnitude:.2f}, {self.angle})"

    def __str__(self):
        return self.__repr__()


class Angle:
    def __init__(self, degrees: float):
        # Normalize angle to be between 0 and 360 degrees
        self.degrees = degrees % 360

    @property
    def angle(self) -> float:
        """Return angle in radians."""
        return math.radians(self.degrees)

    def __add__(self, other: Angle) -> Angle:
        return Angle(self.degrees + other.degrees)

    def __sub__(self, other: Angle) -> Angle:
        return Angle(self.degrees - other.degrees)

    def __repr__(self):
        return f"Angle({self.degrees:.2f}°)"

    def __str__(self):
        return self.__repr__()


@dataclass
class PhysicsState:
    """Stores the current physics state of the body"""

    position: PolarVector
    velocity: PolarVector
    acceleration: PolarVector
    applied_force: PolarVector


class CircleBody:
    def __init__(self, x: float, y: float, radius: float, mass: float):
        self.radius = radius
        self.mass = mass

        # Convert initial cartesian position to PolarVector
        self.position = PolarVector.from_cartesian(x, y)

        # Motion vectors
        self.velocity = PolarVector(0, Angle(0))
        self.acceleration = PolarVector(0, Angle(0))
        self.applied_force = PolarVector(0, Angle(0))
        self.last_force = PolarVector(0, Angle(0))

        # Force calculation callback
        self._force_callback: Optional[Callable[[CircleBody, float], PolarVector]] = (
            None
        )

        # Update listener callback
        self._update_listeners: list[Callable[[CircleBody], None]] = []

    @property
    def x(self) -> float:
        return self.position.x

    @property
    def y(self) -> float:
        return self.position.y

    @property
    def cartesian_position(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def set_force_callback(self, callback: Callable[[CircleBody, float], PolarVector]):
        self._force_callback = callback

    def add_update_listener(self, listener: Callable[[CircleBody], None]):
        self._update_listeners.append(listener)

    def apply_force(self, force: PolarVector):
        self.applied_force = force
        self.last_force = force

    def get_state(self) -> PhysicsState:
        return PhysicsState(
            position=self.position,
            velocity=self.velocity,
            acceleration=self.acceleration,
            applied_force=self.last_force,
        )

    def calculate_acceleration(self, force: PolarVector) -> PolarVector:
        """Calculate acceleration from force (F = ma)"""
        if force.magnitude > 0:
            return PolarVector(force.magnitude / self.mass, force.angle)
        return PolarVector(0, Angle(0))

    def update(self, dt: float):
        """
        Update the physics state using Velocity Verlet integration.
        This method is more stable for orbital motion than basic Euler integration.
        """
        # Get force at current position
        if self._force_callback:
            force = self._force_callback(self, dt)
            self.apply_force(force)

        # Calculate current acceleration
        self.acceleration = self.calculate_acceleration(self.applied_force)

        # Update position using current velocity and acceleration
        new_x = self.x + self.velocity.x * dt + 0.5 * self.acceleration.x * dt * dt
        new_y = self.y + self.velocity.y * dt + 0.5 * self.acceleration.y * dt * dt

        # Calculate new force at updated position
        self.position = PolarVector.from_cartesian(new_x, new_y)
        if self._force_callback:
            new_force = self._force_callback(self, dt)
        else:
            new_force = PolarVector(0, Angle(0))

        # Calculate new acceleration
        new_acceleration = self.calculate_acceleration(new_force)

        # Update velocity using average of accelerations
        new_vel_x = (
            self.velocity.x + 0.5 * (self.acceleration.x + new_acceleration.x) * dt
        )
        new_vel_y = (
            self.velocity.y + 0.5 * (self.acceleration.y + new_acceleration.y) * dt
        )

        # Update state
        self.velocity = PolarVector.from_cartesian(new_vel_x, new_vel_y)
        self.acceleration = new_acceleration
        self.applied_force = PolarVector(0, Angle(0))

        # Update listeners
        for listener in self._update_listeners:
            listener(self)

    def apply_drag(self, coefficient: float = 0.1):
        """Apply drag force opposite to velocity"""
        if self.velocity.magnitude > 0:
            drag_force = (
                -coefficient * self.velocity.magnitude * self.velocity.magnitude
            )
            drag_angle = self.velocity.angle + Angle(180)  # Opposite to velocity
            self.apply_force(PolarVector(drag_force, drag_angle))

    def apply_central_force(self, center_x: float, center_y: float, magnitude: float):
        """Apply a force toward or away from a point (positive = attractive, negative = repulsive)"""
        dx = center_x - self.x
        dy = center_y - self.y
        angle = Angle(math.atan2(dy, dx) * 180 / math.pi)
        force = PolarVector(magnitude, angle)
        self.apply_force(force)


# Example force callbacks:


def orbital_force(center_x: float, center_y: float, magnitude: float):
    """Creates a callback that applies a central force for orbital motion"""

    def force_func(body: CircleBody, dt: float) -> PolarVector:
        dx = center_x - body.x
        dy = center_y - body.y
        distance = math.sqrt(dx * dx + dy * dy)

        # Avoid division by zero
        if distance < 1:
            return PolarVector(0, Angle(0))

        # F = GMm/r^2 style force
        force_magnitude = magnitude / (distance * distance)
        angle = Angle(math.atan2(dy, dx) * 180 / math.pi)

        return PolarVector(force_magnitude, angle)

    return force_func


def harmonic_force(
    center_x: float, center_y: float, k: float
) -> Callable[[CircleBody, float], PolarVector]:
    """Creates a callback that applies a spring-like force (F = -kx)"""

    def force_func(body: CircleBody, dt: float) -> PolarVector:
        dx = center_x - body.x
        dy = center_y - body.y
        distance = math.sqrt(dx * dx + dy * dy)

        # Spring force
        force_magnitude = k * distance
        angle = Angle(math.atan2(dy, dx) * 180 / math.pi)

        return PolarVector(force_magnitude, angle)

    return force_func
