"""handle activity on a connection"""
from abc import ABC, abstractmethod
import asyncio
import logging
import time

from aiolistener.exception import ProtocolError


log = logging.getLogger(__name__)


def _sequence(current=1):
    """generate a sequence of request ids"""
    while True:
        yield current
        current += 1


connection_sequence = _sequence()
packet_sequence = _sequence()


class Connection(ABC):
    """create a single connection"""

    def __init__(self, reader, writer):
        self.id = next(connection_sequence)  # pylint: disable=invalid-name
        self.reader = reader
        self.writer = writer
        self.peerhost, self.peerport = writer.get_extra_info("peername")[:2]

    async def setup(self):
        """perform async connection setup"""
        self.reader = await self.setup_reader()
        self.writer = await self.setup_writer()

    async def setup_reader(self):
        """perform reader setup"""
        return self.reader

    async def setup_writer(self):
        """perform writer setup"""
        return self.writer

    @abstractmethod
    async def next_packet(self):
        """return next packet from connection"""

    @abstractmethod
    async def handle(self, packet, packet_id):
        """handle a single packet"""

    def on_exception(self, exc):
        """deal with general Exception"""


async def on_connection(listener, reader, writer):
    """handle activity on listener connection"""
    con = listener.connection_factory(reader, writer)
    await con.setup()
    log.info("open server=%s socket=%s:%s, cid=%s", listener.name,
             con.peerhost, con.peerport, con.id)
    t_start = time.perf_counter()

    while await handle_packet(con):
        pass

    await writer.drain()
    t_elapsed = time.perf_counter() - t_start
    log.info("close cid=%s, t=%f", con.id, t_elapsed)
    writer.close()


async def handle_packet(con):
    """handle next packet"""

    keep_alive = False
    try:
        packet = await con.next_packet()
        if packet:
            packet_id = next(packet_sequence)
            keep_alive = await con.handle(packet, packet_id)
        else:
            log.info("remote close, cid=%s", con.id)
    except ProtocolError:
        log.info("bad packet close, cid=%s", con.id)
    except asyncio.exceptions.TimeoutError:
        log.info("timeout close, cid=%s", con.id)
    except Exception as exc:  # pylint: disable=broad-except
        log.exception("internal error, cid=%s", con.id)
        try:
            con.on_exception(exc)
        except Exception:  # pylint: disable=broad-except
            log.exception("failure generating exception response")

    return keep_alive
