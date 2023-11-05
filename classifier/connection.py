"""Helper functions to send and receive objects over socket streams."""
import asyncio
import base64
import logging
import os
import socket
from asyncio.exceptions import IncompleteReadError
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Tuple
from uuid import UUID

import joblib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

LOG = logging.getLogger("connections")

INT_LENGTH = 8

SALT = os.environ.get("SALT", "wYfJIy4Nx1hPcxiljwg").encode()
ITERATIONS = int(os.environ.get("KDF_ITERATIONS", "0")) or 1 << 18
FERNET_TTL = int(os.environ.get("FERNET_TTL", 0)) or 60  # Seconds


@dataclass
class Command:
    name: str
    uuid: UUID
    payload: Any = None


@dataclass
class Result:
    payload: Any
    uuid: UUID


@dataclass
class ServerException:
    error: str
    uuid: UUID


class Closed:
    pass


def gen_key(secret: str):
    """Return a key derived from the secert."""
    kdf = PBKDF2HMAC(
        hashes.SHA256(),
        32,
        salt=SALT,
        iterations=ITERATIONS,
    )
    return Fernet(base64.urlsafe_b64encode(kdf.derive(secret.encode())))


def pack_obj(obj, secret: Fernet) -> Tuple[int, bytes]:
    """Packs an object for sending and returns the size and the data"""
    LOG.debug("Opening BytesIo object")
    with BytesIO() as io:
        LOG.debug("Dumping object with joblib")
        joblib.dump(obj, io, compress=True)
        LOG.debug("Seeking to start of io object")
        io.seek(0)
        LOG.debug("Encrypt io object")
        data = secret.encrypt(io.getvalue())
    size = len(data)
    return size, data


async def send_obj(writer: asyncio.StreamWriter, obj: Any, secret: Fernet) -> None:
    """Send object over the writer. first the size and after that the data."""
    LOG.debug("Packing object with secret.")
    size, data = pack_obj(obj, secret)

    LOG.debug("Sending %d bytes of data.", size)

    writer.write(size.to_bytes(INT_LENGTH, "big"))
    writer.write(data)

    await writer.drain()


def send_obj_sync(writer: socket.socket, obj: Any, secret: Fernet) -> None:
    """Sends an object to another socket synchronously."""
    (
        size,
        data,
    ) = pack_obj(obj, secret)

    writer.sendall(size.to_bytes(INT_LENGTH, "big"))
    writer.sendall(data)


async def receive_obj(reader: asyncio.StreamReader, secret: Fernet) -> Any:
    """Receive an object over the reader."""
    try:
        size = int.from_bytes(await reader.readexactly(INT_LENGTH), "big")
    except IncompleteReadError:
        return None

    if size == 0:
        LOG.info("Command with size 0 received, return None")
        return None

    LOG.debug("Expecting %d bytes of data", size)

    with BytesIO() as io:
        data = secret.decrypt(await reader.readexactly(size), FERNET_TTL)
        io.write(data)
        io.seek(0)
        LOG.debug("Received %d bytes of data", size)

        obj = joblib.load(io)

    return obj


def receive_obj_sync(reader: socket.socket, secret: Fernet) -> Any:
    """Receive an object over the socket synchronously."""
    size = int.from_bytes(reader.recv(INT_LENGTH, socket.MSG_WAITALL), "big")

    if size == 0:
        LOG.info("Command with size 0 received, return None")
        return None

    LOG.info(f"Received: {size} bytes")
    with BytesIO() as io:
        data = secret.decrypt(reader.recv(size, socket.MSG_WAITALL), FERNET_TTL)
        io.write(data)
        io.seek(0)
        obj = joblib.load(io)  # nosec

    return obj


async def receive_command(
    reader: asyncio.StreamReader, secret: Fernet
) -> Command | None:
    """Waits for the sender to send a command object."""
    cmd = await receive_obj(reader, secret)

    if isinstance(cmd, Command):
        return cmd

    if cmd is None:
        return None

    raise Exception(f"Received unknown object: {cmd}")


async def receive_result(
    reader: asyncio.StreamReader, secret: Fernet
) -> Result | Closed:
    """Receive a result over the reader."""
    result = await receive_obj(reader, secret)

    if result is None:
        return Closed()

    if isinstance(result, Result):
        return result

    raise Exception(f"Received unknown object: {result}")


def receive_result_sync(reader: socket.socket, secret: Fernet) -> Result | Closed:
    """Receive a result over the reader synchronously."""
    result = receive_obj_sync(reader, secret)

    if result is None:
        return Closed()

    if isinstance(result, Result) or isinstance(result, Closed):
        return result

    if isinstance(result, Exception):
        raise result

    raise Exception(f"Received unknown object: {result}")


async def send_command(
    writer: asyncio.StreamWriter, cmd: Command, secret: Fernet
) -> None:
    """Send the command over the writer."""
    await send_obj(writer, cmd, secret)


def send_command_sync(writer: socket.socket, cmd: Command, secret: Fernet) -> None:
    """Send the command over the writer synchronously."""
    send_obj_sync(writer, cmd, secret)


async def send_result(
    writer: asyncio.StreamWriter, result: Closed | Result | Exception, secret: Fernet
) -> None:
    """Send the result over the writer."""
    await send_obj(writer, result, secret)


async def send_close(writer: asyncio.StreamWriter) -> None:
    """Sends an empty object to signal closing of the connection and then close the writer."""
    writer.write((0).to_bytes(INT_LENGTH, "big"))
    await writer.drain()
    writer.close()

    await writer.wait_closed()


def send_close_sync(writer: socket.socket) -> None:
    """Sends an empty object to signal closing of the connection and then close the writer synchronously."""
    writer.sendall((0).to_bytes(INT_LENGTH, "big"))
    writer.close()
