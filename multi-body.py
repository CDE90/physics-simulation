import math

import pygame

from draw import draw_circle, draw_line
from object import Angle, CircleBody, PolarVector
from trail import SmoothTrail, SmoothTrailWithGlow, Trail

WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
PINK = (255, 0, 255)
YELLOW = (255, 255, 0)
TEXTCOLOR = (0, 0, 0)
(width, height) = (1200, 800)
background_color = BLACK
G = 1000  # Gravitational constant (adjusted for pixels)

# Initialize Pygame
pygame.init()
window = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()
pygame.display.set_caption("Multiple Body Simulation")

# Create circle with proper initial conditions
center_x, center_y = width // 2, height // 2
start_offset = 200

circle1 = CircleBody(x=center_x, y=center_y, radius=20, mass=500)

initial_velocity1 = PolarVector(0, Angle(0))
circle1.velocity = initial_velocity1

# Create a second circle with slightly different initial conditions
circle2 = CircleBody(
    x=center_x + start_offset, y=center_y + start_offset, radius=15, mass=50
)

initial_velocity2 = PolarVector(30, Angle(90))
circle2.velocity = initial_velocity2

# Create a third circle
circle3 = CircleBody(
    x=center_x - start_offset, y=center_y - start_offset, radius=10, mass=30
)

initial_velocity3 = PolarVector(25, Angle(-45))
circle3.velocity = initial_velocity3


def gravitational_force(*bodies: CircleBody):
    """Calculates gravitational force between multiple bodies"""

    def force_func(body: CircleBody, dt: float) -> PolarVector:
        # Initialize resultant force
        resultant_force = PolarVector(0, Angle(0))

        # Calculate force from each other body
        for other_body in bodies:
            # Skip if it's the same body
            if other_body == body:
                continue

            # Calculate the distance between the two bodies
            dx = other_body.x - body.x
            dy = other_body.y - body.y
            distance = math.sqrt(dx * dx + dy * dy)

            # Avoid division by zero
            if distance < 1:
                continue

            # Calculate the gravitational force
            force_magnitude = G * body.mass * other_body.mass / (distance * distance)
            angle = Angle(math.atan2(dy, dx) * 180 / math.pi)

            # Add this force to the resultant
            resultant_force = resultant_force + PolarVector(force_magnitude, angle)

        return resultant_force

    return force_func


force_between_circles = gravitational_force(circle1, circle2, circle3)
circle1.set_force_callback(force_between_circles)
circle2.set_force_callback(force_between_circles)
circle3.set_force_callback(force_between_circles)


class CircleContainer:
    def __init__(
        self,
        circle: CircleBody,
        trail: Trail | SmoothTrail | SmoothTrailWithGlow,
        circle_color: tuple,
    ):
        self.circle = circle
        self.trail = trail
        self.circle_color = circle_color


circles: list[CircleContainer] = []

circles.extend(
    [
        CircleContainer(
            circle=circle1,
            trail=SmoothTrailWithGlow(
                circle1, max_length=1000, color=PINK, width=1, glow_radius=15
            ),
            circle_color=PINK,
        ),
        CircleContainer(
            circle=circle2,
            trail=SmoothTrailWithGlow(
                circle2, max_length=1000, color=YELLOW, width=1, glow_radius=15
            ),
            circle_color=YELLOW,
        ),
        CircleContainer(
            circle=circle3,
            trail=SmoothTrailWithGlow(
                circle3, max_length=1000, color=BLUE, width=1, glow_radius=15
            ),
            circle_color=BLUE,
        ),
    ]
)

running = True
accumulated_time: float = 0


def draw_debug_vectors(window, circle: CircleBody):
    """Draw velocity and acceleration vectors for debugging"""
    # # Draw orbit center
    # draw_circle(window, center_x, center_y, 5, RED)

    # Draw velocity vector (green)
    vel_scale = 1
    end_x = circle.x + circle.velocity.x * vel_scale
    end_y = circle.y + circle.velocity.y * vel_scale
    draw_line(window, circle.x, circle.y, end_x, end_y, GREEN)

    # Draw acceleration vector (red)
    acc_scale = 2
    if circle.acceleration.magnitude > 0:
        acc_end_x = circle.x + circle.acceleration.x * acc_scale
        acc_end_y = circle.y + circle.acceleration.y * acc_scale
        draw_line(window, circle.x, circle.y, acc_end_x, acc_end_y, RED)

    # Draw force vector (white)
    force_scale = 0.1
    if circle.last_force.magnitude > 0:
        force_end_x = circle.x + circle.last_force.x * force_scale
        force_end_y = circle.y + circle.last_force.y * force_scale
        draw_line(window, circle.x, circle.y, force_end_x, force_end_y, WHITE)


FPS = 60
PHYSICS_STEPS_PER_FRAME = 16  # Simulate physics multiple times per frame
dt = 1 / (FPS * PHYSICS_STEPS_PER_FRAME)  # Smaller time step


while running:
    window.fill(background_color)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Use fixed time step for more stable physics
    dt = 1 / FPS  # 60 FPS
    accumulated_time += clock.get_time() / 1000.0

    # Update physics
    for circle_container in circles:
        for _ in range(PHYSICS_STEPS_PER_FRAME):
            circle = circle_container.circle
            circle.update(dt)

    # Draw everything
    for circle_container in circles:
        # Draw orbit path (optional)
        # draw_circle(
        #     window, center_x, center_y, int(orbit_radius), (50, 50, 50), filled=False
        # )

        circle = circle_container.circle
        trail = circle_container.trail

        trail.draw(window)

        # Draw the circle
        draw_circle(
            window,
            int(circle.x),
            int(circle.y),
            circle.radius,
            circle_container.circle_color,
        )

        # Draw debug vectors
        draw_debug_vectors(window, circle)

        # Print debug info
        print(
            f"Displacement: {circle.position.magnitude:.2f} @ {circle.position.angle.degrees:.1f}°, "
            f"Velocity: {circle.velocity.magnitude:.2f} @ {circle.velocity.angle.degrees:.1f}°, "
            f"Force: {circle.last_force.magnitude:.2f} @ {circle.last_force.angle.degrees:.1f}°"
        )

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
