from django import VERSION as DJANGO_VERSION

if DJANGO_VERSION[:2] < (1, 11):
    from django.core.urlresolvers import reverse
else:
    from django.urls import reverse


reverse = reverse
