from typing import ByteString
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
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import generics
from rest_framework.renderers import JSONRenderer
from .usage import human_timedelta, uptime, usage
import datetime, string, random, urllib
from io import StringIO, BytesIO

# variables
ACCEPTED_CONTENT = ['image/jpeg', 'image/png', 'image/gif']

# API ----------------------------------
def generate_name(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def check_content_type(url):
    return str(requests.head(url, allow_redirects=True).headers.get('content-type'))

# image-manipulation
class Triggered(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        try:
            # checking if the image query is supplied
            if 'image' not in request.GET:
                return JsonResponse({"detail":"missing image query."}, status=status.HTTP_400_BAD_REQUEST)
            url = request.GET.get("image")

            # checking content type
            if check_content_type(url) not in ACCEPTED_CONTENT: return JsonResponse({"detail":"invalid image content type."}, status=status.HTTP_400_BAD_REQUEST)

            # doing all the stuff
            with Image.open(requests.get(url, stream=True).raw) as image, Image.open("api/utilities/triggered.png") as triggered, Image.open("api/utilities/red.jpg") as red:
                filename = generate_name()
                image = image.resize(red.size)
                image = image.convert("RGB")
                image.paste(triggered, (0, 181))
                image = Image.blend(image.convert("RGBA"), red.convert("RGBA"), alpha=.4)
                image.save(f'files/{filename}.png', quality=95)

            usage['triggered'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
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
            # checking if the image query is supplied
            if 'image' not in request.GET:
                return JsonResponse({"detail":"missing image query."}, status=status.HTTP_400_BAD_REQUEST)
            url = request.GET.get("image")

            # checking content type
            if check_content_type(url) not in ACCEPTED_CONTENT: return JsonResponse({"detail":"invalid image content type."}, status=status.HTTP_400_BAD_REQUEST)

            # blurring the picture
            with Image.open(requests.get(url, stream=True).raw) as image:
                filename = generate_name()
                image = image.resize((255, 255))
                image = (image.convert('RGB')).filter(ImageFilter.GaussianBlur(2))
                image.save(f'files/{filename}.png', quality=95)

            usage['blur'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
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
            # checking if the image query is supplied
            if 'image' not in request.GET:
                return JsonResponse({"detail":"missing image query."}, status=status.HTTP_400_BAD_REQUEST)
            url = request.GET.get("image")

            # checking content type
            if check_content_type(url) not in ACCEPTED_CONTENT: return JsonResponse({"detail":"invalid image content type."}, status=status.HTTP_400_BAD_REQUEST)

            # resizing the image and then scaling it back, saving and sending the picture
            with Image.open(requests.get(url, stream=True).raw) as image:
                filename = generate_name()
                image = image.resize((255, 255))
                small_image = image.resize((32,32),resample=Image.BILINEAR)
                image = small_image.resize(image.size,Image.NEAREST)
                image.save(f'files/{filename}.png', quality=95)

            usage['pixelate'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
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
            # checking if the image query is supplied
            if 'image' not in request.GET:
                return JsonResponse({"detail":"missing image query."}, status=status.HTTP_400_BAD_REQUEST)
            url = request.GET.get("image")

            # checking content type
            if check_content_type(url) not in ACCEPTED_CONTENT: return JsonResponse({"detail":"invalid image content type."}, status=status.HTTP_400_BAD_REQUEST)

            # doing all the necessary stuff
            # if there is no type query, we flip the image horizontally, if there is however, we check whether it is horizontal or vertical
            # if it is not vertical or horizontal, we return http code 400 bad request
            with Image.open(requests.get(url, stream=True).raw) as image:
                filename = generate_name()
                image = image.resize((255, 255))
                if 'type' in request.GET:
                    flip_type = request.GET.get("type")
                    if flip_type == 'horizontal':
                        image = image.transpose(Image.FLIP_LEFT_RIGHT)
                    elif flip_type == 'vertical':
                        image = image.transpose(Image.FLIP_TOP_BOTTOM)
                    else:
                        return JsonResponse({"detail":"invalid type query."}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    image = image.transpose(Image.FLIP_LEFT_RIGHT)
                image.save(f'files/{filename}.png', quality=95)

            usage['flip'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
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
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        try:
            # checking if the image query is supplied
            if 'image' not in request.GET:
                return JsonResponse({"detail":"missing image query."}, status=status.HTTP_400_BAD_REQUEST)
            url = request.GET.get("image")

            # checking content type
            if check_content_type(url) not in ACCEPTED_CONTENT: return JsonResponse({"detail":"invalid image content type."}, status=status.HTTP_400_BAD_REQUEST)

            # doing all the rotating stuff
            # if there is no type query, we rotate the image 90 degrees to the right, if there is however, we check whether it is left or right
            # if it is not left or right, we return http code 400 bad request
            with Image.open(requests.get(url, stream=True).raw) as image:
                filename = generate_name()
                image = image.resize((255, 255))
                if 'type' in request.GET:
                    rotate_type = request.GET.get("type")
                    if rotate_type == 'left':
                        image = (image.rotate(-90)).convert('RGB')
                    elif rotate_type == 'right':
                        image = (image.rotate(90)).convert('RGB')
                    else:
                        return JsonResponse({"detail":"invalid type query."}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    image = (image.rotate(90)).convert('RGB')
                image.save(f'files/{filename}.png', quality=95)
            
            usage['rotate'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                os.remove(f"files/{filename}.png")
            except:
                pass

    def post(self, request):
        # not allowing methods other than GET
        return JsonResponse({"detail":"Method \"POST\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class Grayscale(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        try:
            # checking if the image query is supplied
            if 'image' not in request.GET:
                return JsonResponse({"detail":"missing image query."}, status=status.HTTP_400_BAD_REQUEST)
            url = request.GET.get("image")

            # checking content type
            if check_content_type(url) not in ACCEPTED_CONTENT: return JsonResponse({"detail":"invalid image content type."}, status=status.HTTP_400_BAD_REQUEST)

            # resizing the picture and applying grayscale effect to it
            with Image.open(requests.get(url, stream=True).raw) as image:
                filename = generate_name()
                image = (image.resize((255, 255))).convert('L')
                image.save(f'files/{filename}.png', quality=95)

            usage['grayscale'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                os.remove(f"files/{filename}.png")
            except:
                pass

    def post(self, request):
        # not allowing methods other than GET
        return JsonResponse({"detail":"Method \"POST\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class Blend(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        try:
            # checking if the image query is supplied
            if 'image' not in request.GET:
                return JsonResponse({"detail":"missing image query."}, status=status.HTTP_400_BAD_REQUEST)
            elif 'image2' not in request.GET:
                return JsonResponse({"detail":"missing image2 query."}, status=status.HTTP_400_BAD_REQUEST)
            url = request.GET.get("image")
            url2 = request.GET.get("image2")

            # checking content type
            if check_content_type(url) not in ACCEPTED_CONTENT: return JsonResponse({"detail":"invalid image content type."}, status=status.HTTP_400_BAD_REQUEST)
            elif check_content_type(url2) not in ACCEPTED_CONTENT: return JsonResponse({"detail":"invalid image2 content type."}, status=status.HTTP_400_BAD_REQUEST)

            # resizing both images, converting them to rgba and then blending them together
            with Image.open(requests.get(url, stream=True).raw) as image, Image.open(requests.get(url2, stream=True).raw) as image2:
                filename = generate_name()
                image = image.resize((255, 255))
                image2 = image2.resize((255, 255))
                final = Image.blend(image.convert("RGBA"), image2.convert("RGBA"), 0.5)
                final.save(f'files/{filename}.png', quality=95)

            usage['blend'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                os.remove(f"files/{filename}.png")
            except:
                pass

    def post(self, request):
        # not allowing methods other than GET
        return JsonResponse({"detail":"Method \"POST\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class Enhance(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        try:
            # checking if the image query is supplied
            if 'image' not in request.GET: return JsonResponse({"detail":"missing image query."}, status=status.HTTP_400_BAD_REQUEST)
            elif 'type' not in request.GET: return JsonResponse({"detail":"missing type query."}, status=status.HTTP_400_BAD_REQUEST)
            elif 'value' not in request.GET: return JsonResponse({"detail":"missing value query."}, status=status.HTTP_400_BAD_REQUEST)
            url = request.GET.get("image")
            try: value = float(request.GET.get("value"))
            except: return JsonResponse({"detail":"value query of incorrect type."}, status=status.HTTP_400_BAD_REQUEST)

            # checking content type
            if check_content_type(url) not in ACCEPTED_CONTENT: return JsonResponse({"detail":"invalid image content type."}, status=status.HTTP_400_BAD_REQUEST)

            # doing all the stuff
            with Image.open(requests.get(url, stream=True).raw) as image:
                filename = generate_name()
                image = image.resize((255, 255))
                enhance_type = request.GET.get("type")
                if enhance_type == 'contrast': image = ImageEnhance.Contrast(image).enhance(value)
                elif enhance_type == 'color': image = ImageEnhance.Color(image).enhance(value)
                elif enhance_type == 'brightness': image = ImageEnhance.Brightness(image).enhance(value)
                elif enhance_type == 'sharpness': image = ImageEnhance.Sharpness(image).enhance(value)
                else: return JsonResponse({"detail":"invalid type query."}, status=status.HTTP_400_BAD_REQUEST)
                image.save(f'files/{filename}.png', quality=95)

            usage['enhance'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                os.remove(f"files/{filename}.png")
            except:
                pass

    def post(self, request):
        # not allowing methods other than GET
        return JsonResponse({"detail":"Method \"POST\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class Invert(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        try:
            # checking if the image query is supplied
            if 'image' not in request.GET:
                return JsonResponse({"detail":"missing image query."}, status=status.HTTP_400_BAD_REQUEST)
            url = request.GET.get("image")

            # checking content type
            if check_content_type(url) not in ACCEPTED_CONTENT: return JsonResponse({"detail":"invalid image content type."}, status=status.HTTP_400_BAD_REQUEST)

            # resizing the image and then converting it to RGB, then inverting its colours
            with Image.open(requests.get(url, stream=True).raw) as image:
                filename = generate_name()
                image = image.resize((255, 255))
                image = image.convert('RGB')
                image = ImageOps.invert(image)
                image.save(f'files/{filename}.png', quality=95)

            usage['invert'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                os.remove(f"files/{filename}.png")
            except:
                pass

    def post(self, request):
        # not allowing methods other than GET
        return JsonResponse({"detail":"Method \"POST\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class GrayscaleInvert(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        try:
            # checking if the image query is supplied
            if 'image' not in request.GET:
                return JsonResponse({"detail":"missing image query."}, status=status.HTTP_400_BAD_REQUEST)
            url = request.GET.get("image")

            # checking content type
            if check_content_type(url) not in ACCEPTED_CONTENT: return JsonResponse({"detail":"invalid image content type."}, status=status.HTTP_400_BAD_REQUEST)

            # resizing the image and then converting it to RGB, then inverting its colours
            with Image.open(requests.get(url, stream=True).raw) as image:
                filename = generate_name()
                image = image.resize((255, 255))
                image = image.convert('L')
                image = ImageOps.invert(image)
                image.save(f'files/{filename}.png', quality=95)

            usage['grayscaleinvert'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                os.remove(f"files/{filename}.png")
            except:
                pass

    def post(self, request):
        # not allowing methods other than GET
        return JsonResponse({"detail":"Method \"POST\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class Emboss(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        try:
            # checking if the image query is supplied
            if 'image' not in request.GET:
                return JsonResponse({"detail":"missing image query."}, status=status.HTTP_400_BAD_REQUEST)
            url = request.GET.get("image")

            # checking content type
            if check_content_type(url) not in ACCEPTED_CONTENT: return JsonResponse({"detail":"invalid image content type."}, status=status.HTTP_400_BAD_REQUEST)

            # resizing the image and then converting it to RGB, then applying the emboss filter to it
            with Image.open(requests.get(url, stream=True).raw) as image:
                filename = generate_name()
                image = image.resize((255, 255))
                image = image = image.convert('RGB').filter(ImageFilter.EMBOSS)
                image.save(f'files/{filename}.png', quality=95)

            usage['emboss'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                os.remove(f"files/{filename}.png")
            except:
                pass

    def post(self, request):
        # not allowing methods other than GET
        return JsonResponse({"detail":"Method \"POST\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class Contour(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        try:
            # checking if the image query is supplied
            if 'image' not in request.GET:
                return JsonResponse({"detail":"missing image query."}, status=status.HTTP_400_BAD_REQUEST)
            url = request.GET.get("image")

            # checking content type
            if check_content_type(url) not in ACCEPTED_CONTENT: return JsonResponse({"detail":"invalid image content type."}, status=status.HTTP_400_BAD_REQUEST)

            # resizing the image and then converting it to RGB, then applying the contour filter to it
            with Image.open(requests.get(url, stream=True).raw) as image:
                filename = generate_name()
                image = image.resize((255, 255))
                image = image = image.convert('RGB').filter(ImageFilter.CONTOUR)
                image.save(f'files/{filename}.png', quality=95)

            usage['contour'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                os.remove(f"files/{filename}.png")
            except:
                pass

    def post(self, request):
        # not allowing methods other than GET
        return JsonResponse({"detail":"Method \"POST\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class Edges(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        try:
            # checking if the image query is supplied
            if 'image' not in request.GET:
                return JsonResponse({"detail":"missing image query."}, status=status.HTTP_400_BAD_REQUEST)
            url = request.GET.get("image")

            # checking content type
            if check_content_type(url) not in ACCEPTED_CONTENT: return JsonResponse({"detail":"invalid image content type."}, status=status.HTTP_400_BAD_REQUEST)

            # resizing the image and then converting it to RGB, then applying the contour filter to it
            with Image.open(requests.get(url, stream=True).raw) as image:
                filename = generate_name()
                image = image.resize((255, 255))
                image = image = image.convert('RGB').filter(ImageFilter.FIND_EDGES)
                image.save(f'files/{filename}.png', quality=95)

            usage['edges'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                os.remove(f"files/{filename}.png")
            except:
                pass

    def post(self, request):
        # not allowing methods other than GET
        return JsonResponse({"detail":"Method \"POST\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)