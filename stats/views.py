from django.http import JsonResponse, HttpResponse
from .celery import index_all_repositories_task


def scan(request):
    code = request.GET.get("code", "")
    if code == "s3cr3t":
        index_all_repositories_task.delay()
        return JsonResponse({"status": "Submitted"})
    else:
        return HttpResponse("Unauthorized", status=401)
