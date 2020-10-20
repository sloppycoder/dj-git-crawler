from django.http import JsonResponse, HttpResponse


def job(request):
    code = request.GET.get("code", "")
    if code == "s3cr3t":
        return JsonResponse({"status": 200})
    else:
        return HttpResponse("Unauthorized", status=401)
