from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from apps.catalogue.sitemaps import GenreSitemap, InstrumentSitemap, SheetMusicSitemap, StaticSitemap
from apps.catalogue import views as catalogue_views

sitemaps = {
    'sheet_music': SheetMusicSitemap,
    'genres': GenreSitemap,
    'instruments': InstrumentSitemap,
    'static': StaticSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),

    # Home & search
    path('', catalogue_views.home, name='home'),
    path('search/', catalogue_views.search, name='search'),

    # Instrument browse (top-level /instruments/)
    path('instruments/', catalogue_views.instruments_browse, name='instruments'),
    path('instruments/<slug:instrument_slug>/', catalogue_views.instrument_list, name='instrument'),

    # Accounts
    path('account/', include('apps.accounts.urls', namespace='accounts')),

    # Catalogue
    path('catalogue/', include('apps.catalogue.urls', namespace='catalogue')),

    # Orders, cart, checkout, webhook
    path('', include('apps.orders.urls', namespace='orders')),

    # Static pages
    path('support/', TemplateView.as_view(template_name='pages/support.html'), name='support'),
    path('privacy-policy/', TemplateView.as_view(template_name='pages/privacy_policy.html'), name='privacy_policy'),
    path('terms-of-service/', TemplateView.as_view(template_name='pages/terms_of_service.html'), name='terms_of_service'),

    # SEO
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
