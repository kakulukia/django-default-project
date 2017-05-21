from django.shortcuts import render

# Create your views here.
def dings(request):
    return render(request, 'index.pug')
