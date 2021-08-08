from django.http.response import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render, redirect
from .forms import CreateUserForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from ratelimit.decorators import ratelimit
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse
import requests, os
from PIL import Image, ImageFilter
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import generics
from rest_framework.renderers import JSONRenderer
from .usage import human_timedelta, uptime, usage
import datetime, string, random

# index
def home(request):
    return render(request, "index.html")

# dashboard
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")
    try:
        token = Token.objects.get(user=request.user).key
    except:
        token = "None"

    # gotta cache these things so it won't hurt my server, but it works for now. (update values once every x minutes)
    total = sum(usage.values())
    minutes_uptime = (datetime.datetime.utcnow() - uptime).total_seconds() / 60.0
    context = {
        "title":"Something API - Dashboard",
        "token":f"{token}",
        "uptime": human_timedelta(uptime),
        "triggered": usage['triggered'],
        "blur": usage['blur'],
        "pixelate": usage['pixelate'],
        "flip": usage['flip'],
        "rotate": usage['rotate'],

        "total": total,
        "average": round(total/minutes_uptime, 1),
      }
    return render(request, "dashboard.html", context)

# documentation
def documentation(request):
    return render(request, "documentation.html")

# registering user
from ratelimit.decorators import ratelimit
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



# API ----------------------------------
def generate_name(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

# image-manipulation
class Triggered(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        try:
            # creating the filename
            if not 'avatar' in request.GET:
                return JsonResponse({"detail":"missing avatar query."}, status=status.HTTP_400_BAD_REQUEST)
            filename = generate_name()

            # opening the avatar and the triggered and red pictures
            triggered = Image.open("api/utilities/triggered.png")
            red = Image.open("api/utilities/red.jpg")
            avatar = Image.open(requests.get(request.GET.get("avatar"), stream=True).raw)

            # pasting one on the other and saving and then sending the response, we also add the red blending
            avatar.paste(triggered, (0, 181))
            avatar = Image.blend(avatar.convert("RGBA"), red.convert("RGBA"), alpha=.4)
            avatar.save(f'files/{filename}.png', quality=95)
            file = open(f'files/{filename}.png', 'rb')

            usage['triggered'] += 1
            return FileResponse(file)
        finally:
            # deleting the created file after sending it
            try:
                os.remove(f"files/{filename}.png")
            except:
                pass

    def post(self, request):
        # not allowing methods other than GET
        return JsonResponse({"detail":"Method \"POST\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class Blur(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        try:
            # creating the filename
            if not 'avatar' in request.GET:
                return JsonResponse({"detail":"missing avatar query."}, status=status.HTTP_400_BAD_REQUEST)
            filename = generate_name()

            # opening the avatar
            avatar = Image.open(requests.get(request.GET.get("avatar"), stream=True).raw)

            # blurring the picture
            avatar = avatar.filter(ImageFilter.GaussianBlur(2))
            avatar.save(f'files/{filename}.png', quality=95)
            file = open(f'files/{filename}.png', 'rb')

            usage['blur'] += 1
            return FileResponse(file)
        finally:
            # deleting the created file after sending it
            try:
                os.remove(f"files/{filename}.png")
            except:
                pass

    def post(self, request):
        # not allowing methods other than GET
        return JsonResponse({"detail":"Method \"POST\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class Pixelate(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        try:
            # creating the filename
            if not 'avatar' in request.GET:
                return JsonResponse({"detail":"missing avatar query."}, status=status.HTTP_400_BAD_REQUEST)
            filename = generate_name()

            # opening the avatar
            avatar = Image.open(requests.get(request.GET.get("avatar"), stream=True).raw)

            # resizing the image and then scaling it back, saving and sending the picture
            small_image = avatar.resize((32,32),resample=Image.BILINEAR)
            avatar = small_image.resize(avatar.size,Image.NEAREST)
            avatar.save(f'files/{filename}.png', quality=95)
            file = open(f'files/{filename}.png', 'rb')

            usage['pixelate'] += 1
            return FileResponse(file)
        finally:
            # deleting the created file after sending it
            try:
                os.remove(f"files/{filename}.png")
            except:
                pass

    def post(self, request):
        # not allowing methods other than GET
        return JsonResponse({"detail":"Method \"POST\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class Flip(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        try:
            # creating the filename
            if 'avatar' not in request.GET:
                return JsonResponse({"detail":"missing avatar query."}, status=status.HTTP_400_BAD_REQUEST)
            filename = generate_name()

            # opening the avatar and the triggered and red pictures
            avatar = Image.open(requests.get(request.GET.get("avatar"), stream=True).raw)

            # if there is no type query, we flip the image horizontally, if there is however, we check whether it is horizontal or vertical
            # if it is not vertical or horizontal, we return http code 400 bad request
            if 'type' in request.GET:
                flip_type = request.GET.get("type")
                if flip_type == 'horizontal':
                    avatar = avatar.transpose(Image.FLIP_LEFT_RIGHT)
                elif flip_type == 'vertical':
                    avatar = avatar.transpose(Image.FLIP_TOP_BOTTOM)
                else:
                    return JsonResponse({"detail":"invalid type query."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                avatar = avatar.transpose(Image.FLIP_LEFT_RIGHT)
            avatar.save(f'files/{filename}.png', quality=95)
            file = open(f'files/{filename}.png', 'rb')

            usage['flip'] += 1
            return FileResponse(file)
        finally:
            # deleting the created file after sending it
            try:
                os.remove(f"files/{filename}.png")
            except:
                pass

    def post(self, request):
        # not allowing methods other than GET
        return JsonResponse({"detail":"Method \"POST\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class Rotate(generics.ListCreateAPIView):
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        try:
            # creating the filename
            if 'avatar' not in request.GET:
                return JsonResponse({"detail":"missing avatar query."}, status=status.HTTP_400_BAD_REQUEST)
            filename = generate_name()

            # opening the avatar and the triggered and red pictures
            avatar = Image.open(requests.get(request.GET.get("avatar"), stream=True).raw)

            # if there is no type query, we rotate the image 90 degrees to the right, if there is however, we check whether it is left or right
            # if it is not left or right, we return http code 400 bad request
            if 'type' in request.GET:
                rotate_type = request.GET.get("type")
                if rotate_type == 'left':
                    avatar = avatar.rotate(-90)
                elif rotate_type == 'right':
                    avatar = avatar.rotate(90)
                else:
                    return JsonResponse({"detail":"invalid type query."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                avatar = avatar.rotate(90)
            avatar.save(f'files/{filename}.png', quality=95)
            file = open(f'files/{filename}.png', 'rb')

            usage['rotate'] += 1
            return FileResponse(file)
        finally:
            # deleting the created file after sending it
            try:
                os.remove(f"files/{filename}.png")
            except:
                pass

    def post(self, request):
        # not allowing methods other than GET
        return JsonResponse({"detail":"Method \"POST\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)