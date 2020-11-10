from django.http import HttpResponse, JsonResponse

from .indexer import active_repos


def repo(request):
    if is_authorized(request):
        repos = [r.repo_url for r in active_repos()]
        return JsonResponse(repos, safe=False)
    else:
        return HttpResponse("Unauthorized", status=401)


def is_authorized(request):
    code = request.GET.get("code", "")
    return code == "s3cr3t"
