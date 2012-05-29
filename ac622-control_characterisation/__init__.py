"""
Characterisation of drone dynamics
==================================

Code for exciting drone and logging sensor outputs.

This package contains functionality for testing drone dynamics.

   - Logger: Scans packets and removes desires sensor readings
   - impulse_response: Applies impulses to the drone using the controlloop module and logs the sent commands
   - plot_response: A matlab script for plotting logged files

.. automodule:: ac622-control_characterisation.Logger
   :members:

.. automodule:: ac622-control_characterisation.impulse_response
   :members:

"""
from . import Logger, impulse_response

__all__ = ['Logger', 'impulse_response',]
