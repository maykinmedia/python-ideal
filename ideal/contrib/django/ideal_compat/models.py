from django.db import models


class Issuer(models.Model):
    code = models.CharField(max_length=11, unique=True)
    name = models.CharField(max_length=35)
    country = models.CharField(max_length=250, db_index=True)
    is_active = models.BooleanField()
