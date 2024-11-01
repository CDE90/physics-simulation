import pygame

import math
from object import CircleBody, PolarVector, Angle, orbital_force

WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
TEXTCOLOR = (0, 0, 0)
(width, height) = (1200, 800)
background_color = BLACK

# Initialize Pygame
pygame.init()
window = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()
pygame.display.set_caption("Orbital Motion Simulation")

# Create circle with proper initial conditions
center_x, center_y = width // 2, height // 2
orbit_radius = 200
circle = CircleBody(x=center_x + orbit_radius, y=center_y, radius=20, mass=1.0)

# Calculate proper initial velocity for circular orbit
# v = sqrt(GM/r) for circular orbit
force_magnitude = 400000  # Increased for more noticeable effect
orbit_velocity = math.sqrt(force_magnitude / (orbit_radius * circle.mass))

# Set initial velocity perpendicular to radius (90 degrees to achieve counterclockwise orbit)
circle.velocity = PolarVector(orbit_velocity, Angle(90))

# Set up orbital force
orbit_force = orbital_force(
    center_x=center_x, center_y=center_y, magnitude=force_magnitude
)
circle.set_force_callback(orbit_force)

circles = [circle]
running = True
accumulated_time: float = 0


def draw_debug_vectors(window, circle: CircleBody):
    """Draw velocity and acceleration vectors for debugging"""
    # Draw orbit center
    pygame.draw.circle(window, RED, (center_x, center_y), 5)

    # Draw velocity vector (green)
    vel_scale = 1
    end_x = circle.x + circle.velocity.x * vel_scale
    end_y = circle.y + circle.velocity.y * vel_scale
    pygame.draw.line(window, GREEN, (circle.x, circle.y), (end_x, end_y), 2)

    # Draw acceleration vector (red)
    acc_scale = 2
    if circle.acceleration.magnitude > 0:
        acc_end_x = circle.x + circle.acceleration.x * acc_scale
        acc_end_y = circle.y + circle.acceleration.y * acc_scale
        pygame.draw.line(window, RED, (circle.x, circle.y), (acc_end_x, acc_end_y), 2)

    # Draw force vector (white)
    force_scale = 1
    if circle.last_force.magnitude > 0:
        force_end_x = circle.x + circle.last_force.x * force_scale
        force_end_y = circle.y + circle.last_force.y * force_scale
        pygame.draw.line(
            window, WHITE, (circle.x, circle.y), (force_end_x, force_end_y), 2
        )


FPS = 60
PHYSICS_STEPS_PER_FRAME = 8  # Simulate physics multiple times per frame


while running:
    window.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Use fixed time step for more stable physics
    dt = 1 / FPS  # 60 FPS
    accumulated_time += clock.get_time() / 1000.0

    # Update physics
    while accumulated_time >= dt:
        for _ in range(PHYSICS_STEPS_PER_FRAME):
            for circle in circles:
                circle.update(dt)
        accumulated_time -= dt

    # Draw everything
    for circle in circles:
        # Draw orbit path (optional)
        pygame.draw.circle(
            window, (50, 50, 50), (center_x, center_y), int(orbit_radius), 1
        )

        # Draw the circle
        pygame.draw.circle(window, BLUE, (int(circle.x), int(circle.y)), circle.radius)

        # Draw debug vectors
        draw_debug_vectors(window, circle)

        # Print debug info
        print(
            f"Velocity: {circle.velocity.magnitude:.2f} @ {circle.velocity.angle.degrees:.1f}°, "
            f"Force: {circle.last_force.magnitude:.2f} @ {circle.last_force.angle.degrees:.1f}°"
        )

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
