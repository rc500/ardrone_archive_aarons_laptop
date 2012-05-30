"""
Drone control and cooperation
=============================

Contains code

This package is made up of the following modules:

  - DroneApp: Defines the configuration of drones in the swarm used for task completion.

  - AppController: Creates objects from the below modules from the specification in the DroneApp module.

  - DroneControl: Sends commands and listens to packets from a drone via the controlloop module.

  - DroneStates: Defines the state of an individual drone based on status messages.

  - SwarmControl: Manages multiple drone controllers to complete a task using logic.

  - SwarmStates: Defines the state of a group (or swarm) of drones in relation to a set task based on status messages.

  - StatusUpdater: Handles raw sensor readings pushed up from the drone and parses them into formats which are useful for different parts of the program. Statuses are then pushed out to DroneControl and SwarmControl objects.

  - ImageProcessor: Processes video frames direct from the drone, pushes output to DroneControl and provides a video feed in an external window. Utilises the aruco library to process reference markers.

  - Navigator: Handles all logic relating to routing over a known mapped area.

  - Controllers: Manages access to a range of controllers which use the DroneControl module to push control inputs to the drone.

It also contains a network_config class where the connection IPs for each drone should be updated before running the application.

.. automodule:: multi_uav.DroneApp
  :members:

.. automodule:: multi_uav.AppController
  :members:

.. automodule:: multi_uav.DroneControl
  :members:

.. automodule:: multi_uav.DroneStates
  :members:

.. automodule:: multi_uav.SwarmControl
  :members:

.. automodule:: multi_uav.SwarmStates
  :members:

.. automodule:: multi_uav.StatusUpdater
  :members:

.. automodule:: multi_uav.ImageProcessor
  :members:

.. automodule:: multi_uav.Navigator
  :members:

.. automodule:: multi_uav.Controllers
  :members:
"""

from . import AppController, SwarmControl, ImageProcessor, DroneControl, DroneApp, Controllers, network_config, DroneStates, SwarmStates, StatusUpdater, Navigator

__all__ = ['AppController', 'SwarmControl', 'ImageProcessor', 'DroneControl', 'DroneApp', 'Controllers', 'network_config', 'DroneStates', 'SwarmStates', 'StatusUpdater', 'Navigator']
