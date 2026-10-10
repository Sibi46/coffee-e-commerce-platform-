from django.contrib import admin
from django.urls import path
from store import views
from store import superadmin
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [path('', views.storefront), path('admin/', admin.site.urls),
               path('super-admin/', superadmin.dashboard, name='superadmin-dashboard'),
               path('super-admin/login/', superadmin.sign_in, name='superadmin-login'),
               path('super-admin/logout/', superadmin.sign_out, name='superadmin-logout'),
               path('api/<str:resource>/', views.api), path('api/<str:resource>/<str:item>/', views.api)]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
