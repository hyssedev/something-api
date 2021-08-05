from django.shortcuts import render

# index
def home(request):
    return render(request, "index.html")