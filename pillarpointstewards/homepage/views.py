from django.shortcuts import render


def index(request):
    return render(request, "index.html")


def patterns(request):
    return render(request, "patterns.html")
