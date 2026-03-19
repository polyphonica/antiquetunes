from django.urls import path
from . import views

app_name = 'bundles'

urlpatterns = [
    path('', views.bundle_list, name='list'),
    path('<slug:slug>/', views.bundle_detail, name='detail'),
]
