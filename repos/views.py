from django.http import JsonResponse
from .models import Author
from .celery import debug_task


def index(request):
    task = debug_task.delay()
    result = task.wait()

    authors = Author.objects.all()
    response = {
        "authors": [{"name": a.name, "email": a.email} for a in authors],
        "task": result
    }
    return JsonResponse(response)
