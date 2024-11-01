import math

import pygame

from draw import draw_circle, draw_line
from object import Angle, CircleBody, PolarVector, orbital_force
from trail import SmoothTrail, SmoothTrailWithGlow, Trail

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

# Calculate proper initial velocity for stable circular orbit
# For a circular orbit, centripetal force = gravitational force
# v = sqrt(GM/r) where G*M is our force_magnitude
force_magnitude = 200000  # Reduced for stability
orbit_velocity = math.sqrt(force_magnitude / orbit_radius)  # Simplified calculation

# Set initial velocity perpendicular to radius
initial_angle = Angle(90)  # 90 degrees for counterclockwise orbit
circle.velocity = PolarVector(orbit_velocity, initial_angle)

# Set up orbital force with proper scaling
orbit_force = orbital_force(
    center_x=center_x, center_y=center_y, magnitude=force_magnitude
)
circle.set_force_callback(orbit_force)

circles = [circle]
circles_trails = [
    SmoothTrailWithGlow(circle, max_length=1000, color=WHITE, width=1, glow_radius=15)
]
running = True
accumulated_time: float = 0


def draw_debug_vectors(window, circle: CircleBody):
    """Draw velocity and acceleration vectors for debugging"""
    # Draw orbit center
    draw_circle(window, center_x, center_y, 5, RED)

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
    force_scale = 1
    if circle.last_force.magnitude > 0:
        force_end_x = circle.x + circle.last_force.x * force_scale
        force_end_y = circle.y + circle.last_force.y * force_scale
        draw_line(window, circle.x, circle.y, force_end_x, force_end_y, WHITE)


FPS = 60
PHYSICS_STEPS_PER_FRAME = 8  # Simulate physics multiple times per frame
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
    for _ in range(PHYSICS_STEPS_PER_FRAME):
        circle.update(dt)

    # Draw everything
    for circle, trail in zip(circles, circles_trails):
        # Draw orbit path (optional)
        # draw_circle(
        #     window, center_x, center_y, int(orbit_radius), (50, 50, 50), filled=False
        # )

        trail.draw(window)

        # Draw the circle
        draw_circle(window, int(circle.x), int(circle.y), circle.radius, WHITE)

        # Draw debug vectors
        # draw_debug_vectors(window, circle)

        # Print debug info
        print(
            f"Velocity: {circle.velocity.magnitude:.2f} @ {circle.velocity.angle.degrees:.1f}°, "
            f"Force: {circle.last_force.magnitude:.2f} @ {circle.last_force.angle.degrees:.1f}°"
        )

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
