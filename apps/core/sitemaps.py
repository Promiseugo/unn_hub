from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from apps.marketplace.models import Listing
from apps.services.models import ServiceOffer
from apps.rentals.models import RentalListing


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return ['landing', 'marketplace:listing-list', 'services:service-list', 'rentals:rental-list']

    def location(self, item):
        return reverse(item)


class ListingSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.6

    def items(self):
        return Listing.objects.filter(
            is_active=True,
            is_sold=False,
            approval_status='approved',
        ).only('pk', 'updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('marketplace:listing-detail', args=[obj.pk])


class ServiceSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return ServiceOffer.objects.filter(
            is_active=True,
            approval_status='approved',
        ).only('pk', 'updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('services:service-detail', args=[obj.pk])


class RentalSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return RentalListing.objects.filter(
            is_active=True,
            is_taken=False,
            approval_status='approved',
        ).only('pk', 'updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('rentals:rental-detail', args=[obj.pk])


sitemaps = {
    'static': StaticViewSitemap,
    'listings': ListingSitemap,
    'services': ServiceSitemap,
    'rentals': RentalSitemap,
}
