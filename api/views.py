from typing import ByteString
from django.http.response import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render, redirect
from .forms import CreateUserForm, KeyRegisterForm
from .models import SubscriptionKeys, Subscriptions
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from ratelimit.decorators import ratelimit
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse
import requests, os
from PIL import Image, ImageFilter, ImageEnhance
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import generics
from rest_framework.renderers import JSONRenderer
from .usage import human_timedelta, uptime, usage
import datetime, string, random, urllib, datetime
from io import StringIO, BytesIO
from django.core.cache import cache

# FRONT-END VIEWS --------------

# index
@ratelimit(key="ip", rate="30/m", method=["GET"], block=True)
def home(request):
    return render(request, "index.html")

# dashboard
@ratelimit(key="ip", rate="15/m", method=["GET", "POST"], block=True)
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")
    form = KeyRegisterForm()

    date_now = datetime.date.today()
    try: 
        user = Subscriptions.objects.get(user=request.user)
        days_left = (user.subscription_end - date_now).days
        token = user.token
    except:
        days_left = None
        token = "None"

    if request.method == 'POST':
        form = KeyRegisterForm(request.POST)
        if form.is_valid():
            # check if user already has an active subscription, if he does, add 30 days to the subscription_end he currently has
            user_exists = Subscriptions.objects.filter(user=request.user)#.update(field2='cool')
            if not user_exists:
                Subscriptions.objects.create(user=request.user, token=Token.objects.create(user=request.user), subscription_start=date_now, subscription_end=date_now+datetime.timedelta(days=30))
            else:
                user = Subscriptions.objects.get(user=request.user)
                subscription_end = user.subscription_end
                user_exists.update(subscription_end=subscription_end + datetime.timedelta(days=30))

            messages.success(request, "Subscription added succesfully.")
            return redirect("dashboard")
    endpoints = [
        "triggered", "blur", "pixelate", "flip", "rotate", "grayscale", "blend", "enhance", "invert", "grayscaleinvert", "emboss", "contour", "edges", "sepia", "colorfilter",
        "gay", "urss", "jail", "missionpassed", "wanted", "wasted", "busted", "simpcard", "hornylicense", "hornylicense2", "whodidthis", "colorviewer"
    ]
    context = {
        "title":"sAPI - Dashboard",
        "token":f"{token}",
        # "uptime": human_timedelta(uptime),
        "form": form,
        "days_left": days_left,
        "endpoint": endpoints,
      }
    return render(request, "dashboard.html", context)

# documentation
@ratelimit(key="ip", rate="30/m", method=["GET"], block=True)
def documentation(request):
    return render(request, "documentation/introduction.html")

@ratelimit(key="ip", rate="30/m", method=["GET"], block=True)
def documentation_auth(request):
    return render(request, "documentation/authorization.html")

@ratelimit(key="ip", rate="30/m", method=["GET"], block=True)
def documentation_errors(request):
    return render(request, "documentation/errors.html")

@ratelimit(key="ip", rate="30/m", method=["GET"], block=True)
def documentation_ratelimits(request):
    return render(request, "documentation/ratelimits.html")

@ratelimit(key="ip", rate="30/m", method=["GET"], block=True)
def documentation_gettingstarted(request):
    return render(request, "documentation/gettingstarted.html")

@ratelimit(key="ip", rate="30/m", method=["GET"], block=True)
def documentation_examples(request):
    return render(request, "documentation/examples.html")

@ratelimit(key="ip", rate="30/m", method=["GET"], block=True)
def documentation_endpoints(request):
    return render(request, "documentation/endpoints.html")

# registering user
@ratelimit(key="ip", rate="5/m", method=["GET", "POST"], block=True)
def register(request):
    form = CreateUserForm()
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account was created succesfully.")
            return redirect("login")

    context = {"form": form}
    return render(request, "register.html", context)

# logging the user in
@ratelimit(key="ip", rate="5/m", method=["GET", "POST"], block=True)
def loginpage(request):
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("index")
        else:
            messages.info(request, "Incorrect credentials.")
            return render(request, "login.html")
    context = {}
    return render(request, "login.html", context)

# logging the user out
def logoutUser(request):
    logout(request)
    return redirect("index")
