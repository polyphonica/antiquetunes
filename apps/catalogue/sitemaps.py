from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Genre, Instrument, SheetMusic


class SheetMusicSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.8

    def items(self):
        return SheetMusic.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class GenreSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return Genre.objects.all()


class InstrumentSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return Instrument.objects.all()


class StaticSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return ['catalogue:list', 'catalogue:instruments', 'support', 'privacy_policy', 'terms_of_service']

    def location(self, item):
        return reverse(item)
