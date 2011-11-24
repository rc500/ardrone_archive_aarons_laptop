Network control protocol
========================

The control system for the drone is split into two programs. The first, and by
far largest, is a single Python program which connects to the drone, allows for
basic resetting and trim control and which parses navigation and video data
received. This program listens on the network on UDP port 5560 for incoming
control packets.

It is envisaged that experimental programs need only send packets to this
control port rather than directly modifying the main program.

Each control packet is formatted as a `JSON document <http://javascript.org/>`_. The
following is the smallest valid document that may be sent:

.. code-block:: javascript

  { "seq": 1 }

The ``seq`` field is a simple sequence number which should be increased by at
least one each time a control packet is sent. The reason is so that control
packets which arrive out-of-order may be discarded.

Setting control state
---------------------

There are three virtual "buttons" which can be pressed: ``take_off``, ``reset``
and ``hover``. When the ``take_off`` button is pressed, the drone will try to
take off if landed and land if flying. When the ``reset`` button is pressed,
the dronegui will attempt to reset all communication with the drone. If the
drone is flying, it will act as if the "emergency" command has been received.
While ``hover`` is pressed, the drone will ignore all control inputs and
attempt to hover in one place.

In addition to the virtual buttons, there are four virtual analogue controls:
``roll``, ``pitch``, ``yaw`` and ``gas``. These may be given floating point
values on the interval [-1,1]. The first two specify the attitude of the drone
as a proportion of the configured maximum roll/pitch angle. This will generally
vary depending on whether the drone is configured for indoor or outdoor flight.
The latter two specify the angular and vertical speeds of the drone, again as a
proportion of configured maxima.

The state of zero, one or more of these controls may be specified by adding a
``state`` field to the JSON document. For example, to indicate that the
``take_off`` button is pressed:

.. code-block:: javascript

  {
    "seq": 1,
    "state": {
      "take_off": True
    }
  }

Similarly, to state that roll and pitch should be set to their maximum:

.. code-block:: javascript

  {
    "seq": 1,
    "state": {
      "hover": False,
      "roll": 1.0,
      "pitch": 1.0
    }
  }

Notice how one must remember to set ``hover`` to false to ensure that the drone
follows your command.

.. vim:spell:spelllang=en_gb
