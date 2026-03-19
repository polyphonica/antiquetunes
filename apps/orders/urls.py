from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('cart/add-bundle/', views.bundle_add, name='bundle_add'),
    path('cart/remove-bundle/<int:bundle_id>/', views.bundle_remove, name='bundle_remove'),
    path('checkout/', views.checkout_create, name='checkout'),
    path('checkout/success/', views.checkout_success, name='checkout_success'),
    path('checkout/cancel/', views.checkout_cancel, name='checkout_cancel'),
    path('webhooks/stripe/', views.stripe_webhook, name='stripe_webhook'),
]
