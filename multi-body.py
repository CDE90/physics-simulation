import math

import pygame

from draw import draw_circle, draw_line
from object import Angle, CircleBody, PolarVector
from trail import SmoothTrailWithGlow

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


class CircleContainer:
    def __init__(
        self,
        circle: CircleBody,
        trail: SmoothTrailWithGlow,
        circle_color: tuple,
    ):
        self.circle = circle
        self.trail = trail
        self.circle_color = circle_color


circles: list[CircleContainer] = []


# ---------- STARTING CONDITIONS ----------


# Create circle with proper initial conditions
center_x, center_y = width // 2, height // 2
start_offset = 200

circle1 = CircleBody(x=center_x, y=center_y, radius=20, mass=400)

initial_velocity1 = PolarVector(20, Angle(0))
circle1.velocity = initial_velocity1

# Create a second circle with slightly different initial conditions
circle2 = CircleBody(
    x=center_x + start_offset, y=center_y + start_offset, radius=15, mass=40
)

initial_velocity2 = PolarVector(35, Angle(90))
circle2.velocity = initial_velocity2

# Create a third circle
circle3 = CircleBody(
    x=center_x - start_offset, y=center_y - start_offset, radius=10, mass=30
)

initial_velocity3 = PolarVector(45, Angle(-60))
circle3.velocity = initial_velocity3


force_between_circles = gravitational_force(circle1, circle2, circle3)
circle1.set_force_callback(force_between_circles)
circle2.set_force_callback(force_between_circles)
circle3.set_force_callback(force_between_circles)

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


class Viewport:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.offset_x: float = 0
        self.offset_y: float = 0

    def update(self, circles: list[CircleContainer]):
        # Calculate center of mass (or average position)
        total_mass: float = 0
        com_x: float = 0
        com_y: float = 0

        for circle_container in circles:
            circle = circle_container.circle
            com_x += circle.x * circle.mass
            com_y += circle.y * circle.mass
            total_mass += circle.mass

        if total_mass > 0:
            com_x /= total_mass
            com_y /= total_mass

            # Calculate desired offset to center the view on COM
            self.offset_x = com_x - self.width / 2
            self.offset_y = com_y - self.height / 2

    def transform(self, x: float, y: float) -> tuple[float, float]:
        """Transform world coordinates to screen coordinates"""
        return (x - self.offset_x, y - self.offset_y)


running = True
accumulated_time: float = 0

viewport = Viewport(width, height)


FPS = 120
PHYSICS_STEPS_PER_FRAME = 8  # Simulate physics multiple times per frame
dt = 1 / (FPS)  # Smaller time step


while running:
    window.fill(background_color)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update viewport position
    viewport.update(circles)

    # Update physics
    for circle_container in circles:
        for _ in range(PHYSICS_STEPS_PER_FRAME):
            circle = circle_container.circle
            circle.update(dt)

    # Draw everything
    for circle_container in circles:
        circle = circle_container.circle
        trail = circle_container.trail

        # Transform coordinates for trail drawing
        trail.draw(window, viewport)

        # Transform coordinates for circle drawing
        screen_x, screen_y = viewport.transform(circle.x, circle.y)
        draw_circle(
            window,
            int(screen_x),
            int(screen_y),
            circle.radius,
            circle_container.circle_color,
        )

        # Draw debug vectors with transformed coordinates
        if circle.velocity.magnitude > 0:
            vel_scale = 1
            start_x, start_y = viewport.transform(circle.x, circle.y)
            end_x, end_y = viewport.transform(
                circle.x + circle.velocity.x * vel_scale,
                circle.y + circle.velocity.y * vel_scale,
            )
            draw_line(window, start_x, start_y, end_x, end_y, GREEN)

        if circle.acceleration.magnitude > 0:
            acc_scale = 2
            start_x, start_y = viewport.transform(circle.x, circle.y)
            end_x, end_y = viewport.transform(
                circle.x + circle.acceleration.x * acc_scale,
                circle.y + circle.acceleration.y * acc_scale,
            )
            draw_line(window, start_x, start_y, end_x, end_y, RED)

        if circle.last_force.magnitude > 0:
            force_scale = 0.1
            start_x, start_y = viewport.transform(circle.x, circle.y)
            end_x, end_y = viewport.transform(
                circle.x + circle.last_force.x * force_scale,
                circle.y + circle.last_force.y * force_scale,
            )
            draw_line(window, start_x, start_y, end_x, end_y, WHITE)

        # print(
        #     f"Displacement: {circle.position.magnitude:.2f} @ {circle.position.angle.degrees:.1f}°, "
        #     f"Velocity: {circle.velocity.magnitude:.2f} @ {circle.velocity.angle.degrees:.1f}°"
        #     f"Force: {circle.last_force.magnitude:.2f} @ {circle.last_force.angle.degrees:.1f}°"
        # )

    pygame.display.flip()
    clock.tick(FPS)


pygame.quit()
