# Physics Simulation

This is a simple physics simulation I've made using Pygame and Python.

There are two examples of a simulation in the `src` folder:

-   `orbital.py`: A simulation of a circle orbiting around a central point.
-   `multi-body.py`: A simulation of multiple circles interacting with each other.

The way the simulation works is using "polar vectors" to represent the position, velocity, acceleration, and force of each object. These vectors store the magnitude and angle of the vector, with helper methods to convert between Cartesian and polar coordinates.

This is less than ideal in reality because all the maths is done using Cartesian coordinates, but I fancied doing it this way for fun.

## Running the simulation

To run the simulation, you need to install the `uv` tool and run the following commands:

```
uv sync
uv run src/multi-body.py
```
