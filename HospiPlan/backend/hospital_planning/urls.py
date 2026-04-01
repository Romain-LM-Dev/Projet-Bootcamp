from django.contrib import admin
from django.urls import path, include
from planning.views import csrf_view 

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/csrf/', csrf_view), 
    path("api/", include("planning.urls")),
]
