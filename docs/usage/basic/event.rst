===============
Event Streaming
===============

The PlanetSide 2 API supports streaming in-game events directly to your client.

This is useful for obtaining real-time event data, but can also be used to gain access to data that would otherwise not be available through the REST API (see the `Examples`_ below).

To gain access to event streaming functionality in Auraxium, you must use the :class:`auraxium.event.EventClient` class. This is a subclass of :class:`auraxium.Client` and still supports the full REST API.

.. note::

   When using the event client, be wary of using the asynchronous context manager interface. When the context manager body finishes execution, the WebSocket connection is shut down as well:

   .. code-block:: python3

      async with auraxium.event.EventClient() as client:
          @client.trigger(...)
          async def action(event):
              ...
         # This block is left immediately, shutting the client

   You can mitigate this by using an :class:`asyncio.Event` or a similar asynchronous flag to keep the control flow within the context manager until you are ready to shut it down.

   Alternatively, you can use :meth:`asyncio.loop.run_forever` to keep the event loop running even after the enclosing method finishes:

   .. code-block:: python3

      loop = asyncio.new_event_loop()
      loop.create_task(main())
      loop.run_forever()

Trigger System Overview
=======================

Auraxium wraps the real-time event endpoint of the PlanetSide 2 API in an event trigger system, which has been inspired by scripting hooks used in many game engines.

.. note::

   Users familiar with the `discord.py <https://github.com/Rapptz/discord.py>`_ package can skip ahead to `Event Types`_ section.

   The system used to define event listeners and commands in d.py is very similar to Auraxium's trigger system, with `Conditions`_ being comparable to d.py's checks.

   Usage examples and the trigger definition syntax are covered further below.

Triggers
--------

Triggers are the main building block of the event streaming interface. They store what events to listen to (e.g. players deaths) and then execute a function when such an event is encountered (e.g. mock them in Discord).

In the case of the PlanetSide 2 event stream, this information is also used to dynamically generate or update the subscription messages needed to receive the appropriate payloads through the WebSocket API.

A trigger can be set up to listen to more than event at once. Information about the event types available and the data they make accessible can be found in the `event types`_ section below.

.. rubric:: Example

The minimum code required to set up an event trigger and its action uses the :meth:`auraxium.event.EventClient.trigger` decorator:

.. code-block:: python3
   :emphasize-lines: 3

   client = auraxium.event.EventClient()

   @client.trigger(auraxium.event.Death)
   async def print_death(event):
         ...  # Do stuff

This version is shortest and will be used for most examples as it covers most use cases, but does not support some advanced trigger features like conditions.

For the full set of features, instantiate the :class:`auraxium.event.Trigger` manually, add any actions and conditions, and finally register it to the client via :meth:`auraxium.event.EventClient.add_trigger`:

.. code-block:: python3
   :emphasize-lines: 3,5,9

   client = auraxium.event.EventClient()

   my_trigger = auraxium.Trigger(auraxium.event.Death)

   @my_trigger.action
   async def print_death(event):
       ...  # Do stuff

   client.add_trigger(my_trigger)

Conditions
----------

Whether a trigger fires is mainly controlled by its events. However, sometimes you may have multiple triggers who's event definitions overlap to some extent.

To keep your event callbacks tidy and not cause unnecessary triggering of potentially expensive actions, you can additionally specify any number of conditions that must be met for the trigger to fire.

Conditions are stored in the :attr:`Trigger.conditions <auraxium.event.Trigger.conditions>` list and are safe to be modified or updated at any point.

This list may contain synchronous callables or any object that evaluates to :obj:`bool`. Callables must take a single argument: the :class:`auraxium.event.Event` encountered.

.. important::

   Coroutines (i.e. functions defined via ``async def``) are **not** supported as conditions and will be cast to :obj:`bool` instead (i.e. always pass).

.. rubric:: Example

.. code-block:: python3
   :emphasize-lines: 3-8,11

   valid_character_ids = [5428072203494645969, ...]

   def check_killer_id(event):
      """Example condition that checks the payload's killing player."""
      payload = event['payload']
      assert payload['event_name'] == 'Death'
      char_id = int(payload['attacker_character_id'])
      return char_id in valid_character_ids

   trigger = auraxium.EventTrigger(auraxium.event.Death)
   trigger.conditions.append(check_killer_id)

   @trigger.action
   async def filtered_death(event):
       ...  # Do stuff

Actions
-------

A trigger action is a method or function that will be run when the corresponding trigger fires (i.e. a matching event is encountered and all conditions were met).

Actions may be synchronous functions or coroutines; anything that is a coroutine as determined by :func:`asyncio.iscoroutinefunction` will be awaited.

The only argument passed to the trigger action is the :class:`auraxium.event.Event` received.

.. rubric:: Example

.. code-block:: python3

   async def example_action(event: Event) -> None:
       """Example function to showcase the signature used for actions.

       Keep in mind that this could also be a regular function (i.e. one
       defined without the "async" keyword).
       """
       # Do stuff

Event Types
===========

You can find a list of all known event types in the :mod:`auraxium.event` module documentation.

Filtering by Experience ID
--------------------------

Due to the high volume of events matching :class:`auraxium.event.GainExperience`, it is also possible to only listen for specific experience IDs.

Due to the dynamic nature of these events, they are not part of the :mod:`auraxium.event` namespace, but are instead generated dynamically via the :meth:`GainExperience.filter_experience <auraxium.event.GainExperience.filter_experience>` method:

.. automethod:: auraxium.event.GainExperience.filter_experience
   :noindex:

The strings generated by this method can then be used in place of :class:`auraxium.event.Event` sub classes to define triggers and conditions.

Examples
========

Levelup Tracker
---------------

A single trigger listening to players gaining a new battle rank and printing the character's name, their title, and the newly gained battle rank.

.. literalinclude:: ../../../examples/rankup_logger.py

Detecting Mutual Deaths
-----------------------

This script listens to player deaths, caching the ones it sees for a few seconds and looking for the opposite death (i.e. another death with the killer and victim reversed).

.. literalinclude:: ../../../examples/mutual_death_detector.py
