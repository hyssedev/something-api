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
ACCEPTED_COLORS = ['red', 'blue', 'green', 'yellow', 'purple']

# API ----------------------------------------------

# functions

# generating temporary filenames
def generate_name(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

# content type checking (gif, png, etc)
def check_content_type(url):
    return str(requests.head(url, allow_redirects=True).headers.get('content-type'))

# sepia function for the sepia endpoint
def sepia(image:Image)->Image:
    width, height = image.size
    pixels = image.load() # create the pixel map

    for py in range(height):
        for px in range(width):
            r, g, b = image.getpixel((px, py))

            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
            tb = int(0.272 * r + 0.534 * g + 0.131 * b)

            if tr > 255:
                tr = 255

            if tg > 255:
                tg = 255

            if tb > 255:
                tb = 255

            pixels[px, py] = (tr,tg,tb)

    return image

def save_image(image, path):
    image.save(path, quality=95)

def delete_image(path):
    os.remove(path)

# colors and the color_filter function for the color filter endpoint
def red(r, g, b):
    newr = r
    return (newr, 0, 0)

def blue(r, g, b):
    newb = b
    return (0, 0, newb)

def green(r, g, b):
    newg = g
    return (0, newg, 0)

def yellow(r, g, b):
    newr = r
    newg = g
    return (newr, newg, 0)

def purple(r, g, b):
    newr = int(r/2)
    newb = int(b/2)
    return (newr, 0, newb)

def color_filter(type:str, image:Image):
    width, height = image.size
    pixels = image.load() # create the pixel map

    for py in range(height):
        for px in range(width):
            r, g, b = image.getpixel((px, py))
            if type == 'red': pixels[px, py] = red(r,g,b)
            elif type == 'blue': pixels[px, py] = blue(r,g,b)
            elif type == 'green': pixels[px, py] = green(r,g,b)
            elif type == 'yellow': pixels[px, py] = yellow(r,g,b)
            elif type == 'purple': pixels[px, py] = purple(r,g,b)
    return image

# ENDPOINTS --------------------------
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
                save_image(image, f'files/{filename}.png')

            usage['triggered'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                delete_image(f"files/{filename}.png")
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
                save_image(image, f'files/{filename}.png')

            usage['blur'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                delete_image(f"files/{filename}.png")
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
                save_image(image, f'files/{filename}.png')

            usage['pixelate'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                delete_image(f"files/{filename}.png")
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
                save_image(image, f'files/{filename}.png')

            usage['flip'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                delete_image(f"files/{filename}.png")
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
                save_image(image, f'files/{filename}.png')
            
            usage['rotate'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                delete_image(f"files/{filename}.png")
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
                save_image(image, f'files/{filename}.png')

            usage['grayscale'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                delete_image(f"files/{filename}.png")
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
                delete_image(f"files/{filename}.png")
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
                save_image(image, f'files/{filename}.png')

            usage['enhance'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                delete_image(f"files/{filename}.png")
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
                save_image(image, f'files/{filename}.png')

            usage['invert'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                delete_image(f"files/{filename}.png")
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
                save_image(image, f'files/{filename}.png')

            usage['grayscaleinvert'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                delete_image(f"files/{filename}.png")
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
                save_image(image, f'files/{filename}.png')

            usage['emboss'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                delete_image(f"files/{filename}.png")
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
                save_image(image, f'files/{filename}.png')

            usage['contour'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                delete_image(f"files/{filename}.png")
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
                save_image(image, f'files/{filename}.png')

            usage['edges'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                delete_image(f"files/{filename}.png")
            except:
                pass

    def post(self, request):
        # not allowing methods other than GET
        return JsonResponse({"detail":"Method \"POST\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class Sepia(generics.ListCreateAPIView):
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
                image = (image.resize((255, 255))).convert('RGB')
                image = sepia(image)
                save_image(image, f'files/{filename}.png')

            usage['sepia'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                delete_image(f"files/{filename}.png")
            except:
                pass

    def post(self, request):
        # not allowing methods other than GET
        return JsonResponse({"detail":"Method \"POST\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class ColorFilter(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        try:
            # checking if the image query is supplied
            if 'image' not in request.GET: return JsonResponse({"detail":"missing image query."}, status=status.HTTP_400_BAD_REQUEST)
            elif 'type' not in request.GET: return JsonResponse({"detail":"missing type query."}, status=status.HTTP_400_BAD_REQUEST)
            url = request.GET.get("image")
            color_type = request.GET.get("type")
            if color_type not in ACCEPTED_COLORS: return JsonResponse({"detail":"invalid type query."}, status=status.HTTP_400_BAD_REQUEST)

            # checking content type
            if check_content_type(url) not in ACCEPTED_CONTENT: return JsonResponse({"detail":"invalid image content type."}, status=status.HTTP_400_BAD_REQUEST)

            # resizing the image and then converting it to RGB, then applying the contour filter to it
            with Image.open(requests.get(url, stream=True).raw) as image:
                filename = generate_name()
                image = (image.resize((255, 255))).convert('RGB')
                image = color_filter(color_type, image)
                save_image(image, f'files/{filename}.png')

            usage['colorfilter'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                delete_image(f"files/{filename}.png")
            except:
                pass

    def post(self, request):
        # not allowing methods other than GET
        return JsonResponse({"detail":"Method \"POST\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class Gay(generics.ListCreateAPIView):
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
            
            # resizing both images, converting them to rgba and then blending them together
            with Image.open(requests.get(url, stream=True).raw) as image, Image.open("api/utilities/gay.png") as gay:
                filename = generate_name()
                image = image.resize(gay.size)
                final = Image.blend(image.convert("RGBA"), gay.convert("RGBA"), 0.5)
                final.save(f'files/{filename}.png', quality=95)

            usage['gay'] += 1
            return FileResponse(open(f'files/{filename}.png', 'rb'))
        finally:
            # deleting the created file after sending it
            try:
                delete_image(f"files/{filename}.png")
            except:
                pass

    def post(self, request):
        # not allowing methods other than GET
        return JsonResponse({"detail":"Method \"POST\" not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)