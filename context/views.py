# Create your views here.
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http.request import HttpRequest
from django.http.response import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from context.forms import SearchForm
from context.models import Realm, Sentence
from context.services import extract_context
from context.vector_store import search_context


@require_GET
def search(request: HttpRequest, realm_slug: str) -> JsonResponse:
    return JsonResponse({})


@require_POST
@login_required
def submit_document(request: HttpRequest, realm_slug: str) -> JsonResponse:
    return JsonResponse({})


@require_POST
@login_required
def submit_url(request: HttpRequest, crawler_pk: str) -> JsonResponse:
    return JsonResponse({})


@login_required
def search_realm(request, slug):
    realm = Realm.objects.get(slug=slug)
    if not request.user.groups.filter(pk=realm.group_id).exists():
        raise PermissionDenied("You don't have access to this page!")

    results = []

    form = SearchForm()

    if request.GET:
        form = SearchForm(request.GET)

        if form.is_valid():
            query = form.cleaned_data["query"]
            k = form.cleaned_data["results"]

            hits = search_context(query, realm, k=k)

            results = []
            for result in hits:
                sentence = Sentence.objects.get(pk=result.id)
                results.append(
                    {
                        "distance": result.distance,
                        "sentence": extract_context(
                            sentence.document.content,
                            sentence.start_position,
                            sentence.length,
                            500,
                        ),
                        "id": sentence.pk,
                        "meta": sentence.document.meta,
                    }
                )

    return render(
        request,
        "context/search.html",
        context={"results": results, "realm": realm, "form": form},
    )
