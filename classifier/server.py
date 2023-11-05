import asyncio
import os
import signal
import traceback
from functools import partial

import joblib
from sentence_transformers import SentenceTransformer
from sklearn.svm import SVC

from classifier.connection import (
    Closed,
    Command,
    Result,
    gen_key,
    receive_command,
    send_result,
)


def _load_classifiers(path):
    return joblib.load(path)


def _store_classifiers(path, classifiers):
    return
    joblib.dump(classifiers, path)


class Server:
    def __init__(self, sbert_model, path, secret, port=9090, host="0.0.0.0") -> None:
        self.sbert_model = SentenceTransformer(sbert_model)

        self.path = path

        if os.path.exists(path):
            self.classifiers = _load_classifiers(path)
        else:
            self.classifiers = dict()

        self.port = port
        self.host = host
        self.secret = gen_key(secret)

    def process_command(self, cmd: Command):
        match cmd.name:
            case "train":
                self.train_classifier(
                    cmd.payload["key"],
                    cmd.payload["samples"],
                    cmd.payload["labels"],
                )
                return Result("done", cmd.uuid)

            case "embedding":
                embedding = self.get_embedding(cmd.payload["sentence"])
                return Result(embedding, cmd.uuid)
            case "predict":
                prediction = self.predict_class(
                    cmd.payload["key"], cmd.payload["sentences"]
                )
                return Result(prediction, cmd.uuid)

            case "connect":
                return Result("success", cmd.uuid)

            case "close":
                return Closed()

            case "ping":
                return Result("pong", cmd.uuid)
        raise ValueError(f"Unknown command: {cmd.name}")

    async def receive(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        cmd = await receive_command(reader, self.secret)

        while cmd is not None:
            try:
                result = self.process_command(cmd)
                if result is not None:
                    await send_result(writer, result, self.secret)

                if isinstance(result, Closed):
                    writer.close()

            except Exception as ex:
                traceback.print_exc()
                await send_result(writer, ex, self.secret)
            cmd = await receive_command(reader, self.secret)

    async def start(self):
        self.server = await asyncio.start_server(self.receive, self.host, self.port)

        async with self.server:
            await self.server.start_serving()
            await self.server.wait_closed()

    def stop(self):
        self.save()
        self.server.close()

    def save(self):
        _store_classifiers(self.path, self.classifiers)

    def predict_class(self, key, values):
        print("Predicting...")
        embedding = self.get_embedding(values)
        result = self.classifiers[key].predict(embedding)
        print(result)
        return result

    def get_embedding(self, sentence):
        return self.sbert_model.encode(sentence)

    def train_classifier(self, key, samples, labels):
        embeddings = self.get_embedding(samples)

        model = SVC()
        model.fit(embeddings, labels)
        self.classifiers[key] = model


def stop(server: Server, _signum):
    """Gracefully shut the server down."""
    server.stop()


async def serve(sbert_model, path, secret, port, host):
    """Main method for the server thread."""

    loop = asyncio.get_running_loop()
    server = Server(sbert_model, path, secret, port, host)

    for signum in [signal.SIGTERM, signal.SIGINT]:
        loop.add_signal_handler(signum, partial(stop, server, signum))

    await server.start()


def main(sbert_model, path, host, port):
    print(sbert_model, path, host, port)
    if host is None:
        host = os.environ.get("API_HOST")
    if port is None:
        port = os.environ.get("API_PORT")
    if sbert_model is None:
        sbert_model = os.environ.get("SBERT_MODEL")

    return asyncio.run(
        serve(sbert_model, path, os.environ.get("API_SECRET"), port, host),
        debug=os.environ.get("LOG_LEVEL") == "DEBUG",
    )
