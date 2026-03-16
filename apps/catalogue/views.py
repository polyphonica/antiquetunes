from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator

from .models import Genre, Category, Instrument, InstrumentFamily, SheetMusic


DECADE_CHOICES = ['1900s', '1910s', '1920s', '1930s', '1940s']
PAGE_SIZE = 24


def _apply_filters(qs, params):
    """Apply URL querystring filters to a SheetMusic queryset."""
    genre = params.get('genre')
    category = params.get('category')
    decade = params.get('decade')
    instrument = params.get('instrument')
    ensemble = params.get('ensemble')
    price_min = params.get('price_min')
    price_max = params.get('price_max')
    sort = params.get('sort', '-created_at')

    if genre:
        qs = qs.filter(genres__slug=genre)
    if category:
        qs = qs.filter(categories__slug=category)
    if decade:
        qs = qs.filter(decade=decade)
    if instrument:
        qs = qs.filter(instruments__slug=instrument)
    if ensemble:
        qs = qs.filter(ensemble_type=ensemble)
    if price_min:
        try:
            qs = qs.filter(price__gte=float(price_min))
        except ValueError:
            pass
    if price_max:
        try:
            qs = qs.filter(price__lte=float(price_max))
        except ValueError:
            pass

    sort_map = {
        'title': 'title',
        '-title': '-title',
        'year': 'year_published',
        '-year': '-year_published',
        'price': 'price',
        '-price': '-price',
        '-created_at': '-created_at',
    }
    qs = qs.order_by(sort_map.get(sort, '-created_at'))

    return qs.distinct()


def home(request):
    featured = SheetMusic.objects.filter(is_active=True, featured=True).prefetch_related('genres')[:6]
    recent = SheetMusic.objects.filter(is_active=True).order_by('-created_at')[:8]
    genres = Genre.objects.all()
    return render(request, 'home.html', {
        'featured': featured,
        'recent': recent,
        'genres': genres,
        'decades': DECADE_CHOICES,
        'instrument_families': InstrumentFamily.choices,
        'seo_title': 'Rare Early 20th Century Sheet Music',
        'seo_description': 'Discover digitised originals from the golden age of popular music — Ragtime, Jazz, Blues, Tin Pan Alley and more.',
    })


def catalogue_list(request):
    qs = SheetMusic.objects.filter(is_active=True).prefetch_related('genres', 'instruments')
    qs = _apply_filters(qs, request.GET)

    paginator = Paginator(qs, PAGE_SIZE)
    page = paginator.get_page(request.GET.get('page'))

    genres = Genre.objects.all()
    categories = Category.objects.filter(parent__isnull=True).prefetch_related('children')
    instruments = Instrument.objects.all()

    return render(request, 'catalogue/list.html', {
        'page_obj': page,
        'genres': genres,
        'categories': categories,
        'instruments': instruments,
        'decades': DECADE_CHOICES,
        'params': request.GET,
        'seo_title': 'Browse Sheet Music',
        'seo_description': 'Browse our collection of rare early 20th century sheet music.',
    })


def genre_list(request, genre_slug):
    genre = get_object_or_404(Genre, slug=genre_slug)
    qs = SheetMusic.objects.filter(is_active=True, genres=genre).prefetch_related('genres', 'instruments')
    qs = _apply_filters(qs, request.GET)

    paginator = Paginator(qs, PAGE_SIZE)
    page = paginator.get_page(request.GET.get('page'))

    instruments = Instrument.objects.filter(sheet_music__genres=genre).distinct()

    return render(request, 'catalogue/list.html', {
        'page_obj': page,
        'active_genre': genre,
        'instruments': instruments,
        'decades': DECADE_CHOICES,
        'params': request.GET,
        'seo_title': f'{genre.name} Sheet Music',
        'seo_description': genre.description or f'Browse {genre.name} sheet music in our collection.',
    })


def instrument_list(request, instrument_slug):
    instrument = get_object_or_404(Instrument, slug=instrument_slug)
    qs = SheetMusic.objects.filter(
        is_active=True, instruments=instrument
    ).prefetch_related('genres', 'instruments')
    qs = _apply_filters(qs, request.GET)

    paginator = Paginator(qs, PAGE_SIZE)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'catalogue/list.html', {
        'page_obj': page,
        'active_instrument': instrument,
        'decades': DECADE_CHOICES,
        'params': request.GET,
        'seo_title': f'{instrument.name} Sheet Music',
        'seo_description': f'Browse sheet music for {instrument.name} in our rare collection.',
    })


def instruments_browse(request):
    all_instruments = Instrument.objects.all()
    grouped = {}
    for inst in all_instruments:
        grouped.setdefault(inst.get_family_display(), []).append(inst)

    return render(request, 'catalogue/instruments.html', {
        'grouped_instruments': grouped,
        'seo_title': 'Browse by Instrument',
        'seo_description': 'Find sheet music by instrument — piano, violin, saxophone, voice and more.',
    })


def sheet_music_detail(request, genre_slug, slug):
    item = get_object_or_404(
        SheetMusic.objects.prefetch_related('genres', 'categories', 'instruments'),
        slug=slug,
        is_active=True,
    )

    related = SheetMusic.objects.filter(
        is_active=True
    ).filter(
        Q(genres__in=item.genres.all()) | Q(instruments__in=item.instruments.all())
    ).exclude(pk=item.pk).distinct()[:4]

    return render(request, 'catalogue/detail.html', {
        'item': item,
        'related': related,
        'breadcrumb_genre': item.genres.first(),
    })


def search(request):
    query = request.GET.get('q', '').strip()
    qs = SheetMusic.objects.filter(is_active=True)

    if query:
        qs = qs.filter(
            Q(title__icontains=query)
            | Q(composer__icontains=query)
            | Q(lyricist__icontains=query)
            | Q(publisher__icontains=query)
            | Q(description__icontains=query)
            | Q(instruments__name__icontains=query)
        ).distinct()

    qs = _apply_filters(qs, request.GET)

    paginator = Paginator(qs, PAGE_SIZE)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'catalogue/search.html', {
        'page_obj': page,
        'query': query,
        'params': request.GET,
        'seo_title': f'Search results for "{query}"' if query else 'Search Sheet Music',
        'seo_description': f'Search results for {query} in AntiqueTunes rare sheet music collection.',
    })
