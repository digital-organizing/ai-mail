from uuid import uuid4

from django.conf import settings
from django.test import SimpleTestCase

from classifier.client import Client, Command, connect

# Create your tests here.


class ClientSimpleTestCase(SimpleTestCase):
    def test_embedding(self):
        with connect(
            settings.API_HOST,
            settings.API_PORT,
            settings.API_SECRET,
        ) as client:
            embedding = client.get_embedding("Hello World!")
            assert embedding.shape[0] == 384
            embeddings = client.get_embedding(["Hello World!", "Das ist ein Test"])
            assert embeddings.shape[0] == 2

    def test_ping(self):
        client = Client(settings.API_HOST, settings.API_PORT, settings.API_SECRET)
        client.connect()
        result = client.ping()
        assert result is not None
        assert result.payload == "pong"
        client.disconnect()

    def test_train_model(self):
        key = "testing"

        sentences = [
            # Sport
            "The soccer team trained hard for the upcoming championship match.",
            "Serena Williams is considered one of the greatest tennis players of all time.",
            "Michael Phelps broke numerous records in Olympic swimming.",
            "Basketball fans eagerly awaited the NBA finals.",
            "The marathon runners trained for months to compete in the Boston Marathon.",
            # Animals
            "The majestic lion is known as the king of the jungle.",
            "Dolphins are known for their intelligence and playful nature.",
            "Elephants are herbivores and have strong social bonds within their herds.",
            "The chameleon can change its color to blend in with its surroundings.",
            "The bald eagle is a symbol of freedom and strength in the United States.",
            # Human Rights
            "Everyone deserves the right to freedom of speech and expression.",
            "Child labor is a grave violation of human rights.",
            "Access to clean water and basic sanitation is a fundamental human right.",
            "Prisoners should be treated with dignity and respect, regardless of their crimes.",
            "Equal pay for equal work is a cornerstone principle in the fight for gender equality.",
        ]
        labels = ["Sport"] * 5 + ["Animals"] * 5 + ["Human Rights"] * 5

        with connect(
            settings.API_HOST,
            settings.API_PORT,
            settings.API_SECRET,
        ) as client:
            client.train_classifier(key, sentences, labels)
            labels_p = client.predict_class(key, sentences)

            for a, b in zip(labels, labels_p):
                assert a == b

            label = client.predict_class(key, [sentences[-1]])

            assert label == "Human Rights"

    def test_server_error(self):
        key = "testing"

        with connect(
            settings.API_HOST,
            settings.API_PORT,
            settings.API_SECRET,
        ) as client:
            self.assertRaises(ValueError, lambda: client.train_classifier(key, [], []))

    def test_close_and_send(self):
        client = Client(settings.API_HOST, settings.API_PORT, settings.API_SECRET)
        client.connect()
        client.disconnect()
        self.assertRaises(OSError, client.ping)

    def test_invalid_cmd(self):
        with connect(
            settings.API_HOST,
            settings.API_PORT,
            settings.API_SECRET,
        ) as client:
            self.assertRaises(
                ValueError,
                lambda: client.send_command(Command("invalid", uuid4(), None)),
            )
