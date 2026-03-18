from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import Customer


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next') or 'home'
            return redirect(next_url)
        messages.error(request, 'Invalid email or password.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        display_name = request.POST.get('display_name', '').strip()

        if not email:
            messages.error(request, 'Email is required.')
        elif password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        elif Customer.objects.filter(email__iexact=email).exists():
            messages.error(request, 'An account with that email already exists.')
        else:
            user = Customer.objects.create_user(
                email=email,
                password=password1,
                display_name=display_name,
            )
            login(request, user, backend='apps.accounts.backends.EmailBackend')
            messages.success(request, 'Welcome to AntiqueTunes!')
            return redirect('home')

    return render(request, 'accounts/register.html')


@login_required
def orders_view(request):
    orders = (
        request.user.orders
        .prefetch_related('items__sheet_music')
        .order_by('-created_at')
    )
    return render(request, 'accounts/orders.html', {
        'orders': orders,
        'seo_title': 'My Orders',
    })


@login_required
def downloads_view(request):
    from apps.orders.models import DownloadToken
    tokens = (
        DownloadToken.objects
        .filter(customer=request.user)
        .select_related('order_item__sheet_music', 'order_item__order')
        .order_by('-created_at')
    )
    return render(request, 'accounts/downloads.html', {
        'tokens': tokens,
        'seo_title': 'My Downloads',
    })
