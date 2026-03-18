from .models import Genre, InstrumentFamily


def navigation(request):
    """Inject genres, instrument families, and cart count into every template context."""
    cart = request.session.get('cart', {})
    return {
        'nav_genres': Genre.objects.all()[:8],
        'instrument_families': InstrumentFamily.choices,
        'cart_count': len(cart),
    }
