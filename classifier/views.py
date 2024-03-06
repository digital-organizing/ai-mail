import io

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponseBadRequest
from django.http.response import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view

from classifier.classify import predict_class, predict_class_proba
from classifier.models import Classifier, Sample


@login_required
def classification_view(request, id):
    return render(request, "classifier/classification.html", {})


@api_view(["GET", "POST"])
@login_required
def classify(request: HttpRequest, pk):
    if request.method == "POST":
        texts = request.data["texts"]
        print(texts)

        if request.GET.get("probas", False):
            result = predict_class_proba(Classifier.objects.get(uuid=pk), texts)
        else:
            result = predict_class(Classifier.objects.get(uuid=pk), texts)
        return JsonResponse({"result": result})
    return render(request, "classifier/send_texts.html")


@login_required
def upload_samples_view(request: HttpRequest, pk):
    model = Classifier.objects.get(uuid=pk)

    if request.method == "POST":
        Sample.objects.filter(classifier=model).delete()

        label_column = request.POST.get("label")
        content_column = request.POST.get("content")

        file_obj = request.FILES.get("file")

        if file_obj is None:
            return JsonResponse({})

        ftype = request.POST.get("ftype", "csv").lower()
        if ftype == "csv":
            df = pd.read_csv(
                io.StringIO(file_obj.read().decode("utf-8")), delimiter=","
            )
        elif ftype == "excel":
            df = pd.read_excel(io.BytesIO(file_obj.read()))
        else:
            return HttpResponseBadRequest()
        df = df.rename(columns={label_column: "label", content_column: "content"})

        samples = []
        for idx, row in df.iterrows():
            samples.append(
                Sample(content=row["content"], label=row["label"], classifier=model)
            )
        Sample.objects.bulk_create(samples)

    return render(request, "classifier/upload_samples.html", {"model": model})
