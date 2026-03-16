from django.urls import path
from . import views

app_name = 'catalogue'

urlpatterns = [
    path('', views.catalogue_list, name='list'),
    path('search/', views.search, name='search'),
    path('instruments/', views.instruments_browse, name='instruments'),
    path('instruments/<slug:instrument_slug>/', views.instrument_list, name='instrument'),
    path('<slug:genre_slug>/', views.genre_list, name='genre'),
    path('<slug:genre_slug>/<slug:slug>/', views.sheet_music_detail, name='detail'),
]
