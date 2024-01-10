from django.urls import path

from classifier.views import classify, upload_samples_view

app_name = "classifier"


urlpatterns = [
    path("classify/<uuid:pk>/", classify, name="classify"),
    path("upload/<uuid:pk>/", upload_samples_view, name="upload"),
]
