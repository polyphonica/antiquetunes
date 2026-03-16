from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomerManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra)


class Customer(AbstractUser):
    """Custom user model — email is the login identifier."""
    username = None
    email = models.EmailField(unique=True)
    objects = CustomerManager()
    display_name = models.CharField(max_length=150, blank=True)

    # Optional billing address for future tax support
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, blank=True, default='US')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        name = f'{self.first_name} {self.last_name}'.strip()
        return name or self.display_name or self.email
