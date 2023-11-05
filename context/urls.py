from django.urls import path

from context.views import search_realm

app_name = "context"

urlpatterns = [
    path("search/<slug:slug>/", search_realm, name="search-realm"),
]
