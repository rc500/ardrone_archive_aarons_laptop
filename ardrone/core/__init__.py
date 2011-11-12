"""Core A.R. drone control code.

This package contains core functionality for controlling the drone. Note that
one generally has to use this package along with ardrone.platform modules in
order to implement a complete solution.

This package is made up of the following modules:

  - atcommands: Abstracts the generation of AT command packets for directly
    controlling the drone.

  - config: ''Work in progress'' Parse the drone configuration when sent to the
    client in a config packet.

  - navdata: Parse navdata navigation packets which are sent by the drone
    contaiing information on its current state.

  - controlloop: Implement the required logic to initiate navigation and video
    data streaming and maintin communication with the drone. In addition,
    implement some convenience wrappers around the functions in atcommands.

  - videopacket: ''Work in progress'' Use the mini-library libp264 shipped with
    these packages to decode ieo packets as they arrive from the drone.

"""

from . import atcommands, config, controlloop, navdata, videopacket

__all__ = ['atcommands', 'config', 'controlloop', 'navdata', 'videopacket']
