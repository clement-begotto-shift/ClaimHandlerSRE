from django.db import models

class Claim(models.Model):
    Id = models.AutoField(primary_key=True)
    ClaimName = models.CharField(max_length=255)
    Verified = models.BooleanField(default=False)