from django.http import JsonResponse, HttpResponse
from .celery import (
    index_all_repositories_task,
    gather_author_stats_task,
    discover_repositories_task,
)


def job(request):
    code = request.GET.get("code", "")
    job = request.GET.get("code", "scan")
    if code == "s3cr3t":
        status = "submitted"
        if job == "scan":
            index_all_repositories_task.delay()
        elif job == "stat":
            gather_author_stats_task.delay([])
        elif job == "discover":
            discover_repositories_task.delay()
        else:
            status = "don't know what to do."
        return JsonResponse({"status": status})
    else:
        return HttpResponse("Unauthorized", status=401)
