from django.test import TestCase

from classifier.classify import train_classifier
from classifier.models import Classifier, Sample

# Create your tests here.


class ClassifierTestCase(TestCase):
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
    samples = zip(labels, sentences)

    def test_train_model(self):
        model = Classifier.objects.create(name="Test", language="german")

        samples = [
            Sample(content=content, label=label, classifier=model)
            for content, label in self.samples
        ]

        Sample.objects.bulk_create(samples)

        train_classifier(model)
