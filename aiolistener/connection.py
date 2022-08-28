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

    def on_open(self, message):
        """handle on-open message"""
        log.info(message)

    def on_remote_close(self):
        """handle remote-close condition"""
        log.info("remote close, cid=%s", self.id)

    def on_close(self, message):
        """handle on-close message"""
        log.info(message)


async def on_connection(listener, reader, writer):
    """handle activity on listener connection

       This is a callback provided to the start_server function when a new
       listener is added with _Listeners.add.

       A new connection instance is created using the specified reader and
       writer along with any *args provided in _Listeners.add. Packets are
       handled sequentially until the handle_packet return is not truthy.
    """
    con = listener.connection(reader, writer, *listener.args)
    await con.setup()
    t_start = time.perf_counter()

    con.on_open(
        f"open server={listener.name}"
        f" socket={con.peerhost}:{con.peerport}"
        f" cid={con.id}")

    while await handle_packet(con):
        pass

    await writer.drain()

    con.on_close(
        f"close cid={con.id}"
        f" t={time.perf_counter() - t_start:.6f}")

    writer.close()


async def handle_packet(con):
    """handle next packet"""

    keep_alive = False
    try:
        if packet := await con.next_packet():
            packet_id = next(packet_sequence)
            keep_alive = await con.handle(packet, packet_id)
        else:
            con.on_remote_close()
    except ProtocolError:
        log.warning("bad packet close, cid=%s", con.id)
    except asyncio.exceptions.TimeoutError:
        log.warning("timeout close, cid=%s", con.id)
    except Exception as exc:  # pylint: disable=broad-except
        log.exception("internal error, cid=%s", con.id)
        try:
            con.on_exception(exc)
        except Exception:  # pylint: disable=broad-except
            log.exception("failure generating exception response")

    return keep_alive
