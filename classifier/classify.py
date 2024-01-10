from io import BytesIO
from typing import List

from django.core.files import File
from laser_encoders import LaserEncoderPipeline
from sklearn.svm import SVC
from sklearn.utils.validation import joblib

from classifier.models import Classifier, Sample


def generate_embeddings(texts: List[str], encoder: LaserEncoderPipeline):
    return encoder.encode_sentences(texts, normalize_embeddings=True)


def train_classifier(model: Classifier):
    samples = Sample.objects.filter(classifier=model)
    encoder = LaserEncoderPipeline(model.language, laser="laser2")

    embeddings = generate_embeddings([sample.content for sample in samples], encoder)

    classifier = SVC()
    classifier.fit(embeddings, [sample.label for sample in samples])

    store_classifier(model, classifier)

    return classifier


def store_classifier(model: Classifier, classifier: SVC):
    out = BytesIO()
    joblib.dump(classifier, out)
    out.seek(0)
    file = File(out, f"{model.uuid}.cpk")
    model.model.save(file.name, file)


def load_classifier(model: Classifier):
    classifier: SVC = joblib.load(model.model)

    return classifier


def predict_class(model: Classifier, texts: List[str]):
    classifier = load_classifier(model)

    encoder = LaserEncoderPipeline(laser="laser2")

    embeddings = generate_embeddings(texts, encoder)

    slugs = classifier.predict(embeddings)

    return slugs
