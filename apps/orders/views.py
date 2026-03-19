import os
from datetime import timedelta

import stripe
from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.db.models import F
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.catalogue.models import Bundle, SheetMusic
from .models import DownloadToken, Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY


# ── Cart helpers ──────────────────────────────────────────────────────────────

def _get_cart(request):
    return request.session.get('cart', {})


def _save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


# ── Cart views ────────────────────────────────────────────────────────────────

def cart_view(request):
    cart = _get_cart(request)
    items = []
    total = 0
    for item_id, data in cart.items():
        price = float(data['price'])
        total += price
        items.append({**data, 'id': item_id, 'price_float': price})

    return render(request, 'orders/cart.html', {
        'cart_items': items,
        'total': total,
        'seo_title': 'Your Cart',
    })


@require_POST
def cart_add(request):
    item_id = request.POST.get('item_id', '').strip()
    if not item_id:
        return redirect('home')

    item = get_object_or_404(SheetMusic, pk=item_id, is_active=True)

    # Block logged-in users from re-purchasing something they already own
    if request.user.is_authenticated:
        already_owns = DownloadToken.objects.filter(
            customer=request.user,
            order_item__sheet_music=item,
        ).exists()
        if already_owns:
            messages.warning(
                request,
                f'You already own "{item.title}". '
                f'<a href="/account/downloads/" class="underline font-semibold">Go to Downloads</a>'
            )
            return redirect(request.META.get('HTTP_REFERER', 'home'))

    cart = _get_cart(request)

    if str(item_id) not in cart:
        first_genre = item.genres.first()
        cart[str(item_id)] = {
            'type': 'sheet_music',
            'title': item.title,
            'composer': item.composer,
            'price': str(item.price),
            'cover_url': item.cover_image.url if item.cover_image else None,
            'slug': item.slug,
            'genre_slug': first_genre.slug if first_genre else None,
        }
        _save_cart(request, cart)
        messages.success(request, f'"{item.title}" added to your cart.')

    return redirect('orders:cart')


@require_POST
def bundle_add(request):
    bundle_id = request.POST.get('bundle_id', '').strip()
    if not bundle_id:
        return redirect('home')

    bundle = get_object_or_404(Bundle, pk=bundle_id, is_active=True)
    cart_key = f'bundle_{bundle_id}'

    # Warn if user already owns some pieces in this bundle
    if request.user.is_authenticated:
        owned = DownloadToken.objects.filter(
            customer=request.user,
            order_item__sheet_music__in=bundle.items.all(),
        ).select_related('order_item__sheet_music').distinct()
        if owned.exists():
            owned_titles = ', '.join(
                t.order_item.sheet_music.title for t in owned if t.order_item.sheet_music
            )
            messages.warning(
                request,
                f'You already own some pieces in this bundle ({owned_titles}). '
                f'You can still purchase it if you wish.'
            )

    cart = _get_cart(request)
    if cart_key not in cart:
        cart[cart_key] = {
            'type': 'bundle',
            'bundle_id': bundle_id,
            'title': bundle.title,
            'price': str(bundle.price),
            'individual_total': str(bundle.individual_total),
            'saving': str(bundle.saving),
            'saving_percent': bundle.saving_percent,
            'piece_count': bundle.piece_count,
            'cover_url': bundle.cover_image.url if bundle.cover_image else None,
            'slug': bundle.slug,
        }
        _save_cart(request, cart)
        messages.success(request, f'"{bundle.title}" bundle added to your cart.')

    return redirect('orders:cart')


@require_POST
def bundle_remove(request, bundle_id):
    cart = _get_cart(request)
    cart.pop(f'bundle_{bundle_id}', None)
    _save_cart(request, cart)
    return redirect('orders:cart')


@require_POST
def cart_remove(request, item_id):
    cart = _get_cart(request)
    cart.pop(str(item_id), None)
    _save_cart(request, cart)
    return redirect('orders:cart')


# ── Checkout ──────────────────────────────────────────────────────────────────

@require_POST
def checkout_create(request):
    cart = _get_cart(request)
    if not cart:
        return redirect('orders:cart')

    sheet_music_ids = []
    bundle_ids = []
    for key, data in cart.items():
        if data.get('type') == 'bundle':
            bundle_ids.append(int(data['bundle_id']))
        else:
            try:
                sheet_music_ids.append(int(key))
            except ValueError:
                pass

    db_items = list(SheetMusic.objects.filter(pk__in=sheet_music_ids, is_active=True)) if sheet_music_ids else []
    db_bundles = list(Bundle.objects.filter(pk__in=bundle_ids, is_active=True).prefetch_related('items')) if bundle_ids else []

    if not db_items and not db_bundles:
        return redirect('orders:cart')

    subtotal = sum(i.price for i in db_items) + sum(b.price for b in db_bundles)
    order = Order.objects.create(
        customer=request.user if request.user.is_authenticated else None,
        status=Order.Status.PENDING,
        subtotal=subtotal,
        total=subtotal,
    )
    order.order_reference = f"AT-{timezone.now().year}-{order.pk:05d}"
    order.save(update_fields=['order_reference'])

    for item in db_items:
        OrderItem.objects.create(order=order, sheet_music=item, unit_price=item.price)

    for bundle in db_bundles:
        for piece in bundle.items.filter(is_active=True):
            OrderItem.objects.create(order=order, sheet_music=piece, bundle=bundle, unit_price=0)

    # Build Stripe line items from live DB prices
    line_items = []
    for item in db_items:
        desc = f"Sheet music by {item.composer}" if item.composer else "Digitised sheet music PDF"
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': item.title,
                    'description': desc,
                },
                'unit_amount': int(item.price * 100),
            },
            'quantity': 1,
        })
    for bundle in db_bundles:
        pieces = list(bundle.items.all()[:3])
        sample = ', '.join(p.title for p in pieces)
        if bundle.piece_count > 3:
            sample += '…'
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': bundle.title,
                    'description': f'{bundle.piece_count} pieces: {sample}',
                },
                'unit_amount': int(bundle.price * 100),
            },
            'quantity': 1,
        })

    checkout_kwargs = {
        'payment_method_types': ['card'],
        'line_items': line_items,
        'mode': 'payment',
        'success_url': f"{settings.SITE_URL}/checkout/success/?session_id={{CHECKOUT_SESSION_ID}}",
        'cancel_url': f"{settings.SITE_URL}/checkout/cancel/",
        'metadata': {'order_id': str(order.pk)},
    }

    if request.user.is_authenticated:
        checkout_kwargs['customer_email'] = request.user.email

    session = stripe.checkout.Session.create(**checkout_kwargs)
    order.stripe_session_id = session.id
    order.save(update_fields=['stripe_session_id'])

    return redirect(session.url, permanent=False)


def checkout_success(request):
    session_id = request.GET.get('session_id', '')
    order = None
    tokens = []

    if session_id:
        try:
            order = Order.objects.prefetch_related('items__sheet_music').get(
                stripe_session_id=session_id
            )
            tokens = list(
                DownloadToken.objects.filter(order_item__order=order)
                .select_related('order_item__sheet_music')
            )
        except Order.DoesNotExist:
            pass

    request.session.pop('cart', None)

    return render(request, 'orders/checkout_success.html', {
        'order': order,
        'tokens': tokens,
        'seo_title': 'Order Confirmed',
    })


def checkout_cancel(request):
    return render(request, 'orders/checkout_cancel.html', {
        'seo_title': 'Checkout Cancelled',
    })


# ── Stripe webhook ────────────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    event_type = event['type']
    obj = event['data']['object']

    if event_type in ('checkout.session.completed', 'checkout.session.async_payment_succeeded'):
        _handle_checkout_completed(obj)
    elif event_type in ('checkout.session.async_payment_failed', 'checkout.session.expired'):
        _handle_checkout_failed_or_expired(obj)
    elif event_type == 'charge.refunded':
        _handle_charge_refunded(obj)

    return HttpResponse(status=200)


def _handle_checkout_completed(session):
    order_id = session.get('metadata', {}).get('order_id')
    if not order_id:
        return

    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        return

    if order.status == Order.Status.PAID:
        return  # idempotency

    if not order.customer:
        customer_details = session.get('customer_details') or {}
        order.guest_email = customer_details.get('email') or ''
    order.stripe_payment_intent_id = session.get('payment_intent') or ''
    order.status = Order.Status.PAID
    order.save(update_fields=['guest_email', 'stripe_payment_intent_id', 'status'])

    for order_item in order.items.select_related('sheet_music'):
        if order.customer:
            DownloadToken.objects.create(
                order_item=order_item,
                customer=order.customer,
                expires_at=None,
                max_downloads=None,
            )
        else:
            DownloadToken.objects.create(
                order_item=order_item,
                customer=None,
                expires_at=timezone.now() + timedelta(days=30),
                max_downloads=5,
            )

    _send_order_confirmation(order)


def _handle_checkout_failed_or_expired(session):
    order_id = session.get('metadata', {}).get('order_id')
    if not order_id:
        return
    Order.objects.filter(
        pk=order_id,
        status=Order.Status.PENDING,
    ).update(status=Order.Status.FAILED)


def _handle_payment_failed(payment_intent):
    pi_id = payment_intent.get('id', '')
    if not pi_id:
        return
    Order.objects.filter(
        stripe_payment_intent_id=pi_id,
        status=Order.Status.PENDING,
    ).update(status=Order.Status.FAILED)


def _handle_charge_refunded(charge):
    pi_id = charge.get('payment_intent', '')
    if not pi_id:
        return
    try:
        order = Order.objects.get(stripe_payment_intent_id=pi_id)
    except Order.DoesNotExist:
        return
    order.status = Order.Status.REFUNDED
    order.save(update_fields=['status'])
    DownloadToken.objects.filter(order_item__order=order).update(
        max_downloads=F('download_count')
    )


def _send_order_confirmation(order):
    recipient = order.email
    if not recipient:
        return

    tokens = list(
        DownloadToken.objects.filter(order_item__order=order)
        .select_related('order_item__sheet_music')
    )
    context = {
        'order': order,
        'tokens': tokens,
        'site_url': settings.SITE_URL,
    }

    subject = f"Your AntiqueTunes order — {order.order_reference}"
    body_txt = render_to_string('emails/order_confirmation.txt', context)
    body_html = render_to_string('emails/order_confirmation.html', context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=body_txt,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    msg.attach_alternative(body_html, 'text/html')
    msg.send(fail_silently=True)


# ── Secure file download ──────────────────────────────────────────────────────

def download_file(request, token):
    token_obj = get_object_or_404(DownloadToken, token=token)

    # Account-linked tokens require the matching logged-in user
    if token_obj.customer:
        if not request.user.is_authenticated or request.user != token_obj.customer:
            return redirect(f'/account/login/?next=/account/downloads/{token}/')

    if not token_obj.is_valid:
        raise Http404("This download link has expired or reached its limit.")

    sheet_music = token_obj.order_item.sheet_music
    if not sheet_music or not sheet_music.pdf_file:
        raise Http404("File not found.")

    token_obj.download_count += 1
    token_obj.save(update_fields=['download_count'])

    filename = f"{sheet_music.slug}.pdf"

    if not settings.DEBUG:
        # Production: Nginx X-Accel-Redirect
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['X-Accel-Redirect'] = f'/protected_media/{sheet_music.pdf_file.name}'
        return response

    # Development: serve directly
    file_path = os.path.join(settings.PROTECTED_MEDIA_ROOT, sheet_music.pdf_file.name)
    if not os.path.exists(file_path):
        raise Http404("File not found.")

    response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
