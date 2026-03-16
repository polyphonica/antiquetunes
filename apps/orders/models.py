import uuid
from django.conf import settings
from django.db import models


class Order(models.Model):
    """Stub model — fully implemented in Phase 2."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        REFUNDED = 'refunded', 'Refunded'
        FAILED = 'failed', 'Failed'

    order_reference = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='orders',
    )
    guest_email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stripe_session_id = models.CharField(max_length=200, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.order_reference

    @property
    def email(self):
        if self.customer:
            return self.customer.email
        return self.guest_email


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    sheet_music = models.ForeignKey(
        'catalogue.SheetMusic', null=True, blank=True, on_delete=models.SET_NULL
    )
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f'{self.order.order_reference} — {self.sheet_music}'


class DownloadToken(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='tokens')
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='download_tokens',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    download_count = models.PositiveIntegerField(default=0)
    max_downloads = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return str(self.token)

    @property
    def is_valid(self):
        from django.utils import timezone
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        if self.max_downloads and self.download_count >= self.max_downloads:
            return False
        return True
