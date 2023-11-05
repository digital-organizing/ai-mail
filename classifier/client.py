import socket
from contextlib import contextmanager
from uuid import uuid4

import numpy as np

from classifier.connection import (
    Closed,
    Command,
    Result,
    gen_key,
    receive_result_sync,
    send_command_sync,
)


class Client:
    def __init__(self, host, port, secret) -> None:
        self.host = host
        self.port = port
        self.key = gen_key(secret)

    def connect(self):
        self.socket = socket.create_connection((self.host, self.port))
        self.send_command(Command("connect", uuid4(), {}))

    def disconnect(self):
        self.send_command(Command("close", uuid4(), None))

    def ping(self):
        return self.send_command(Command("ping", uuid4(), None))

    def send_command(self, command: Command) -> Result | None:
        send_command_sync(self.socket, command, self.key)
        result = receive_result_sync(self.socket, self.key)

        if isinstance(result, Closed):
            self.socket.close()
            return None

        return result

    def predict_class(self, key, values):
        uuid = uuid4()
        result = self.send_command(
            Command("predict", uuid, {"key": key, "sentences": values})
        )

        if result is None:
            raise ValueError("No result returned!")

        return result.payload

    def get_embedding(self, sentence) -> np.ndarray:
        uuid = uuid4()

        result = self.send_command(Command("embedding", uuid, {"sentence": sentence}))

        if result is None:
            raise ValueError("No result returned!")

        return result.payload

    def train_classifier(self, key, samples, labels, config=None):
        if config is None:
            config = {}
        uuid = uuid4()
        return self.send_command(
            Command(
                "train",
                uuid,
                {
                    "key": key,
                    "samples": samples,
                    "labels": labels,
                },
            )
        )


@contextmanager
def connect(host, port, secret):
    """Provides a context manager for a client connection to host and port"""
    client = Client(host, port, secret)
    client.connect()
    try:
        yield client
    finally:
        client.disconnect()
