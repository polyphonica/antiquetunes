import os
from decimal import Decimal
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models import Sum
from django.utils.text import slugify

protected_storage = FileSystemStorage(
    location=settings.PROTECTED_MEDIA_ROOT,
    base_url=None,  # never publicly accessible
)


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = 'Genres'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('catalogue:genre', kwargs={'genre_slug': self.slug})


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='children'
    )
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        if self.parent:
            return f'{self.parent.name} > {self.name}'
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class InstrumentFamily(models.TextChoices):
    KEYBOARD = 'keyboard', 'Keyboard'
    STRINGS = 'strings', 'Strings'
    WOODWIND = 'woodwind', 'Woodwind'
    BRASS = 'brass', 'Brass'
    PERCUSSION = 'percussion', 'Percussion'
    VOICE = 'voice', 'Voice'
    ENSEMBLE = 'ensemble', 'Orchestra / Band / Ensemble'


class Instrument(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    family = models.CharField(max_length=20, choices=InstrumentFamily.choices)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['family', 'display_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('catalogue:instrument', kwargs={'instrument_slug': self.slug})


class EnsembleType(models.TextChoices):
    SOLO = 'solo', 'Solo'
    DUO = 'duo', 'Duo'
    TRIO = 'trio', 'Trio'
    QUARTET = 'quartet', 'Quartet'
    QUINTET = 'quintet', 'Quintet'
    VOICE_PIANO = 'voice_piano', 'Voice & Piano'
    CHAMBER = 'chamber', 'Chamber Group'
    ORCHESTRA = 'orchestra', 'Orchestra'
    BAND = 'band', 'Band'
    CHOIR = 'choir', 'Choir'
    UNSPECIFIED = 'unspecified', 'Unspecified'


def sheet_music_pdf_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f'sheet_music/pdf/{instance.slug}{ext}'


def sheet_music_cover_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f'sheet_music/covers/{instance.slug}{ext}'


def sheet_music_preview_image_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f'sheet_music/previews/img/{instance.slug}{ext}'


def sheet_music_preview_pdf_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f'sheet_music/previews/pdf/{instance.slug}{ext}'


def sheet_music_audio_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f'sheet_music/audio/{instance.slug}{ext}'


class SheetMusic(models.Model):
    # Core identity
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)

    # Creators
    composer = models.CharField(max_length=255)
    lyricist = models.CharField(max_length=255, blank=True)
    arranger = models.CharField(max_length=255, blank=True)

    # Publication
    publisher = models.CharField(max_length=255, blank=True)
    year_published = models.PositiveSmallIntegerField(null=True, blank=True)
    decade = models.CharField(max_length=10, blank=True, editable=False)

    # Classification
    genres = models.ManyToManyField(Genre, blank=True, related_name='sheet_music')
    categories = models.ManyToManyField(Category, blank=True, related_name='sheet_music')
    instruments = models.ManyToManyField(Instrument, blank=True, related_name='sheet_music')
    ensemble_type = models.CharField(
        max_length=20, choices=EnsembleType.choices,
        default=EnsembleType.UNSPECIFIED, blank=True
    )

    # Description
    description = models.TextField(blank=True)
    condition_notes = models.TextField(blank=True)

    # Pricing
    price = models.DecimalField(max_digits=8, decimal_places=2)

    # Files — cover images are public, PDF is protected
    cover_image = models.ImageField(upload_to=sheet_music_cover_path, blank=True)
    preview_image = models.ImageField(
        upload_to=sheet_music_preview_image_path, blank=True, editable=False
    )
    preview_pdf = models.FileField(
        upload_to=sheet_music_preview_pdf_path, blank=True, editable=False
    )
    audio_sample = models.FileField(upload_to=sheet_music_audio_path, blank=True)
    pdf_file = models.FileField(upload_to=sheet_music_pdf_path, storage=protected_storage, blank=True)

    # Metadata
    page_count = models.PositiveSmallIntegerField(null=True, blank=True)

    # Status
    is_active = models.BooleanField(default=False)
    featured = models.BooleanField(default=False)

    # SEO overrides
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Sheet Music'
        verbose_name_plural = 'Sheet Music'

    def __str__(self):
        return f'{self.title} — {self.composer}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug()
        if self.year_published:
            self.decade = f'{(self.year_published // 10) * 10}s'
        if not self.meta_description and self.description:
            self.meta_description = self.description[:155].strip()
        super().save(*args, **kwargs)

    def _unique_slug(self):
        base = slugify(f'{self.title} {self.composer}')
        slug = base
        n = 1
        while SheetMusic.objects.filter(slug=slug).exists():
            slug = f'{base}-{n}'
            n += 1
        return slug

    def get_absolute_url(self):
        from django.urls import reverse
        from django.conf import settings
        primary_genre = self.genres.first()
        genre_slug = primary_genre.slug if primary_genre else 'uncategorised'
        path = reverse('catalogue:detail', kwargs={
            'genre_slug': genre_slug,
            'slug': self.slug,
        })
        site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
        return f'{site_url}{path}' if site_url else path

    @property
    def seo_title(self):
        if self.meta_title:
            return self.meta_title
        parts = [self.title, self.composer]
        if self.year_published:
            parts.append(str(self.year_published))
        return ' — '.join(parts)

    @property
    def seo_description(self):
        if self.meta_description:
            return self.meta_description
        return self.description[:155].strip() if self.description else ''

    @property
    def instrument_list(self):
        return ', '.join(self.instruments.values_list('name', flat=True))


def bundle_cover_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f'bundles/covers/{instance.slug}{ext}'


class Bundle(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to=bundle_cover_path, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    items = models.ManyToManyField(SheetMusic, related_name='bundles', blank=True)
    is_active = models.BooleanField(default=False)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('bundles:detail', kwargs={'slug': self.slug})

    @property
    def individual_total(self):
        return self.items.aggregate(total=Sum('price'))['total'] or Decimal('0')

    @property
    def saving(self):
        return self.individual_total - self.price

    @property
    def saving_percent(self):
        individual = self.individual_total
        if individual:
            return int((self.saving / individual) * 100)
        return 0

    @property
    def piece_count(self):
        return self.items.count()
