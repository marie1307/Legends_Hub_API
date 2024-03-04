from django.db import models
from django.contrib.auth.models import AbstractUser

# CustomUser - add in_game_name as required field and full-name field 
class CustomUser(AbstractUser):
    in_game_name = models.CharField(
        max_length=20, unique=True, verbose_name="ingame name")
    full_name = models.CharField(
        max_length=100, unique=True, verbose_name="full name")

    def __str__(self):
        return self.in_game_name
