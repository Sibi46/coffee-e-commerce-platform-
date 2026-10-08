from django.contrib import admin
from django.urls import path
from store import views

urlpatterns = [path('', views.storefront), path('admin/', admin.site.urls),
               path('api/<str:resource>/', views.api), path('api/<str:resource>/<str:item>/', views.api)]
