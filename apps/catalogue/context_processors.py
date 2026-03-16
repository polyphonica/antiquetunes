from .models import Genre, InstrumentFamily


def navigation(request):
    """Inject genres and instrument families into every template context."""
    return {
        'nav_genres': Genre.objects.all()[:8],
        'instrument_families': InstrumentFamily.choices,
    }
