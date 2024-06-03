"""
URL configuration for grip_link_demo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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

from grip_link_demo.views import SSEIsExpiredView, SSESpecializedChannelView

urlpatterns = [
    path("events/is-expired/", SSEIsExpiredView.as_view(), name="streaming-is-expired-channel"),
    path("events/<str:channel_uuid>/", SSESpecializedChannelView.as_view(), name="streaming-specialized-channel"),
]
