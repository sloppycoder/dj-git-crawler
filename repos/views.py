from django.http import JsonResponse
from .models import Author


def index(request):
    authors = Author.objects.all()
    response = {
        "authors": [{"name": a.name, "email": a.email} for a in authors],
    }
    return JsonResponse(response)
