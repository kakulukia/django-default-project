from django.shortcuts import render


def server_error(request):
    return render(request, "500.pug", status=500)
