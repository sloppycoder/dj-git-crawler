from django.http import JsonResponse, HttpResponse
from .models import Author
from .celery import discover_repositories_task, index_all_repositories_task


def index(request):
    authors = Author.objects.all()
    response = {
        "authors": [{"name": a.name, "email": a.email} for a in authors],
    }
    return JsonResponse(response)


def discover(request):
    code = request.GET.get("code", "")
    if code == "s3cr3t":
        discover_repositories_task.delay()
        return JsonResponse({"status": "Submitted"})
    else:
        return HttpResponse("Unauthorized", status=401)


def scan(request):
    code = request.GET.get("code", "")
    if code == "s3cr3t":
        index_all_repositories_task.delay()
        return JsonResponse({"status": "Submitted"})
    else:
        return HttpResponse("Unauthorized", status=401)
