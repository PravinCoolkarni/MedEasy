from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(200)], default=18)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')], default='Male')
    mobile_regex = RegexValidator(regex=r'^\d{10}$', message="Mobile number must be exactly 10 digits.")
    mobile = models.CharField(validators=[mobile_regex], max_length=10, default='0000000000')

    def __str__(self):
        return f'{self.user.username} Profile'
