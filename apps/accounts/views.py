from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
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
            _merge_guest_orders(request, user, email)
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

            # Guest-to-account merge: link any past guest orders to this account
            _merge_guest_orders(request, user, email)

            messages.success(request, 'Welcome to AntiqueTunes!')
            return redirect('home')

    return render(request, 'accounts/register.html')


def _merge_guest_orders(request, user, email):
    """Link paid guest orders to a newly registered account and upgrade tokens."""
    from apps.orders.models import DownloadToken, Order

    guest_orders = Order.objects.filter(
        guest_email__iexact=email,
        status=Order.Status.PAID,
    )
    merged_count = 0
    for order in guest_orders:
        order.customer = user
        order.guest_email = ''
        order.save(update_fields=['customer', 'guest_email'])
        # Upgrade guest tokens to permanent account tokens
        DownloadToken.objects.filter(
            order_item__order=order,
            customer=None,
        ).update(
            customer=user,
            expires_at=None,
            max_downloads=None,
        )
        merged_count += 1

    if merged_count:
        noun = 'order' if merged_count == 1 else 'orders'
        messages.info(
            request,
            f'Your {merged_count} previous {noun} have been linked to your account '
            f'and your downloads are now permanent.',
        )


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


@login_required
def profile_view(request):
    user = request.user

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            display_name = request.POST.get('display_name', '').strip()
            email = request.POST.get('email', '').strip()

            if not email:
                messages.error(request, 'Email address is required.')
            elif Customer.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                messages.error(request, 'That email address is already in use.')
            else:
                user.display_name = display_name
                user.email = email
                user.save(update_fields=['display_name', 'email'])
                messages.success(request, 'Your profile has been updated.')

        elif action == 'change_password':
            current_password = request.POST.get('current_password', '')
            new_password1 = request.POST.get('new_password1', '')
            new_password2 = request.POST.get('new_password2', '')

            if not user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password1 != new_password2:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password1) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
            else:
                user.set_password(new_password1)
                user.save()
                update_session_auth_hash(request, user)  # keep user logged in
                messages.success(request, 'Your password has been changed.')

        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {
        'seo_title': 'My Profile',
    })
