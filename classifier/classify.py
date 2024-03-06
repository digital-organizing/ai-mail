from io import BytesIO
from typing import List

import numpy as np
from django.core.files import File
from laser_encoders import LaserEncoderPipeline
from sklearn.base import ClassifierMixin
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.utils.validation import joblib

from classifier.models import Classifier, Sample


def generate_embeddings(texts: List[str], encoder: LaserEncoderPipeline):
    return encoder.encode_sentences(texts, normalize_embeddings=True)


def find_classifier(X, y):
    candidates = [
        RandomForestClassifier(max_depth=7),
        RandomForestClassifier(max_depth=10),
        KNeighborsClassifier(),
        GradientBoostingClassifier(),
        SVC(probability=True),
    ]
    max_score = -np.inf
    best_model = None

    for candidate in candidates:
        score = np.mean(cross_val_score(candidate, X, y))
        if score > max_score:
            score = max_score
            best_model = candidate

    assert best_model is not None

    return best_model.fit(X, y)


def train_classifier(model: Classifier):
    samples = Sample.objects.filter(classifier=model)
    encoder = LaserEncoderPipeline(model.language, laser="laser2")

    embeddings = generate_embeddings([sample.content for sample in samples], encoder)

    X = embeddings
    y = [sample.label for sample in samples]
    classifier = find_classifier(X, y)

    y_pred = classifier.predict_proba(X)
    mapping = {slug: i for i, slug in enumerate(classifier.classes_)}
    locator = [mapping[name] for name in y]
    probas = np.array([d[i] for d, i in zip(y_pred, locator)])

    for sample, label, proba in zip(samples, y, probas):
        print(sample.label, label, proba, sample.content)

    model.min_threshold = probas.min()
    store_classifier(model, classifier)

    return classifier


def store_classifier(model: Classifier, classifier: ClassifierMixin):
    out = BytesIO()
    joblib.dump(classifier, out)
    out.seek(0)
    file = File(out, f"{model.uuid}.cpk")
    model.model.save(file.name, file)


def load_classifier(model: Classifier):
    classifier: RandomForestClassifier = joblib.load(model.model)

    return classifier


def predict_class(model: Classifier, texts: List[str]):
    classifier = load_classifier(model)

    encoder = LaserEncoderPipeline(laser="laser2")

    embeddings = generate_embeddings(texts, encoder)

    slugs = classifier.predict(embeddings)

    return list(slugs)


def predict_class_proba(model: Classifier, texts: List[str]):
    classifier = load_classifier(model)

    encoder = LaserEncoderPipeline(laser="laser2")

    embeddings = generate_embeddings(texts, encoder)

    probas = classifier.predict_proba(embeddings)

    labels = [classifier.classes_[i] for i in np.argmax(probas, axis=1)]
    scores = np.max(probas, axis=1)

    return [{"slug": label, "score": score} for label, score in zip(labels, scores)]
