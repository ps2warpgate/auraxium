"""A Python wrapper for the PlanetSide 2 API.

This module provides an intuitive, object-oriented interface for using
the Census API. It targets interactive or medium traffic use-cases such
as Discord bots, player and outfit trackers, or aggregation of
historical data for AI purposes.

This is explicitly not targeting higher traffic use cases like website
back-ends, experiment at your own risk.

For additional information, bug reports or feature requests, visit the
project's repository at https://github.com/leonhard-s/auraxium.
"""

from . import census

__all__ = ['census']
__author__ = 'Leonhard S.'
__version__ = '0.1.0a0'
