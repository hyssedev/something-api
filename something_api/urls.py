"""something_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from api import views
from api import views_api

urlpatterns = [
    # front-end
    path('admin/', admin.site.urls),
    path('', views.home, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('documentation/', views.documentation, name='documentation'),
    path('documentation/authorization', views.documentation_auth, name='documentation/authorization'),
    path('documentation/errors', views.documentation_errors, name='documentation/errors'),
    path('documentation/ratelimits', views.documentation_ratelimits, name='documentation/ratelimits'),
    path('documentation/gettingstarted', views.documentation_gettingstarted, name='documentation/gettingstarted'),

    # user register login logout
    path('register/', views.register, name='register'),
    path('login/', views.loginpage, name='login'),
    path('logout/', views.logoutUser, name='logout'),

    # endpoints
    path('api/image-manipulation/triggered', views_api.Triggered.as_view(), name='triggered'),
    path('api/image-manipulation/blur', views_api.Blur.as_view(), name='blur'),
    path('api/image-manipulation/pixelate', views_api.Pixelate.as_view(), name='pixelate'),
    path('api/image-manipulation/flip', views_api.Flip.as_view(), name='flip'),
    path('api/image-manipulation/rotate', views_api.Rotate.as_view(), name='rotate'),
    path('api/image-manipulation/grayscale', views_api.Grayscale.as_view(), name='grayscale'),
    path('api/image-manipulation/blend', views_api.Blend.as_view(), name='blend'),
    path('api/image-manipulation/enhance', views_api.Enhance.as_view(), name='enhance'),
    path('api/image-manipulation/invert', views_api.Invert.as_view(), name='invert'),
    path('api/image-manipulation/grayscaleinvert', views_api.GrayscaleInvert.as_view(), name='grayscaleinvert'),
    path('api/image-manipulation/emboss', views_api.Emboss.as_view(), name='emboss'),
    path('api/image-manipulation/contour', views_api.Contour.as_view(), name='contour'),
    path('api/image-manipulation/edges', views_api.Edges.as_view(), name='edges'),
    path('api/image-manipulation/sepia', views_api.Sepia.as_view(), name='sepia'),
    path('api/image-manipulation/colorfilter', views_api.ColorFilter.as_view(), name='colorfilter'),
    path('api/image-manipulation/gay', views_api.Gay.as_view(), name='gay'),
    path('api/image-manipulation/urss', views_api.Urss.as_view(), name='urss'),
    path('api/image-manipulation/jail', views_api.Jail.as_view(), name='jail'),
    path('api/image-manipulation/missionpassed', views_api.MissionPassed.as_view(), name='missionpassed'),
    path('api/image-manipulation/wanted', views_api.Wanted.as_view(), name='wanted'),
    path('api/image-manipulation/wasted', views_api.Wasted.as_view(), name='wasted'),
    path('api/image-manipulation/busted', views_api.Busted.as_view(), name='busted'),
    path('api/image-manipulation/simpcard', views_api.SimpCard.as_view(), name='simpcard'),
    path('api/image-manipulation/hornylicense', views_api.HornyLicense.as_view(), name='hornylicense'),
    path('api/image-manipulation/hornylicense2', views_api.HornyLicense2.as_view(), name='hornylicense2'),
    path('api/image-manipulation/whodidthis', views_api.WhoDidThis.as_view(), name='whodidthis'),
]
