from django.urls import path

from . import views
from apps.orders.views import download_file

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('orders/', views.orders_view, name='orders'),
    path('downloads/', views.downloads_view, name='downloads'),
    path('downloads/<uuid:token>/', download_file, name='download'),
]
