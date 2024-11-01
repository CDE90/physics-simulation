from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Optional, Tuple


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
        self.last_force = PolarVector(0, Angle(0))  # Store last force for debugging

        # Force calculation callback
        self._force_callback: Optional[Callable[[CircleBody, float], PolarVector]] = (
            None
        )

    @property
    def x(self) -> float:
        """Get x coordinate from polar position"""
        return self.position.x

    @property
    def y(self) -> float:
        """Get y coordinate from polar position"""
        return self.position.y

    @property
    def cartesian_position(self) -> Tuple[float, float]:
        """Get position as cartesian coordinates"""
        return (self.x, self.y)

    def set_force_callback(self, callback: Callable[[CircleBody, float], PolarVector]):
        """
        Set a callback that will be called during update to calculate forces.
        Callback should take (circle_body, dt) and return a PolarVector force.
        """
        self._force_callback = callback

    def apply_force(self, force: PolarVector):
        """Apply an instantaneous force to the body"""
        self.applied_force = force
        self.last_force = force  # Store for debugging

    def get_state(self) -> PhysicsState:
        """Get the current physics state"""
        return PhysicsState(
            position=self.position,
            velocity=self.velocity,
            acceleration=self.acceleration,
            applied_force=self.last_force,  # Use last force for debugging
        )

    def update(self, dt: float):
        """
        Update the physics state for this time step.
        Args:
            dt: Time step in seconds
        """
        # Get force from callback if one is set
        if self._force_callback:
            force = self._force_callback(self, dt)
            self.apply_force(force)

        # Calculate acceleration from force (F = ma)
        if self.applied_force.magnitude > 0:
            self.acceleration = PolarVector(
                self.applied_force.magnitude / self.mass, self.applied_force.angle
            )

        # Update velocity using acceleration
        # v = v0 + at
        new_vel_x = self.velocity.x + self.acceleration.x * dt
        new_vel_y = self.velocity.y + self.acceleration.y * dt
        self.velocity = PolarVector.from_cartesian(new_vel_x, new_vel_y)

        # Update position using velocity
        # x = x0 + vt + (1/2)at^2
        new_x = self.x + self.velocity.x * dt + 0.5 * self.acceleration.x * dt * dt
        new_y = self.y + self.velocity.y * dt + 0.5 * self.acceleration.y * dt * dt
        self.position = PolarVector.from_cartesian(new_x, new_y)

        # Reset applied force after applying it, but keep last_force for debugging
        self.applied_force = PolarVector(0, Angle(0))

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
