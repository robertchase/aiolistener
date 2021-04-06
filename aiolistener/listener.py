"""listening socket functions"""
import asyncio
from functools import partial
import logging

from aiolistener.connection import on_connection


log = logging.getLogger(__name__)


class Listener:  # pylint: disable=too-few-public-methods
    """listener class"""

    def __init__(self, name, port, connection_factory):
        self.name = name
        self.port = int(port)
        self.connection_factory = connection_factory
        self.server = None


class _Listeners:
    """setup and run listeners"""

    def __init__(self):
        self.listeners = []

    async def add(self, name, port, connection):
        """start a listener on a port"""
        listener = Listener(name, port, connection)
        log.info("starting server '%s' on port %d", listener.name,
                 listener.port)
        callback = partial(on_connection, listener)
        listener.server = await asyncio.start_server(
            callback, port=listener.port)
        log.info('listening on %s', listener.server.sockets[0].getsockname())
        self.listeners.append(listener)

    async def run(self):
        """listen forever on all the added connections"""
        await asyncio.gather(
            *[listener.server.serve_forever() for listener in self.listeners])


Listeners = _Listeners()
