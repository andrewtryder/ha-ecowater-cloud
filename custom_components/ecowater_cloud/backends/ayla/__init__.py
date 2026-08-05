"""Ayla IoT Platform backend adapter.

Satisfies the :class:`~custom_components.ecowater_cloud.backends.BackendAdapter`
protocol.
"""

from .backend import AylaBackend

__all__ = ["AylaBackend"]
