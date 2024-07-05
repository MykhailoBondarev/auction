from django.contrib.auth.models import AbstractUser
from django.db import models
import os
import datetime

def _content_file_name(instance, filename):
    now = datetime.datetime.now()
    y = now.year
    M = now.month
    d = now.day
    h = now.hour
    m = now.minute
    s = now.second
    ms = now.microsecond
    ext = filename.split('.')[-1]
    filename = "%s_%s.%s" % ("Image", f"{h}{m}{s}{ms}", ext)
    path = os.path.join(f'{y}/{M}/{d}', filename)    
    return path

class User(AbstractUser):
    icon = models.ImageField(blank=True, upload_to=_content_file_name, default="no-icon.jpg")

class Category(models.Model):
    name = models.CharField(max_length=64)
    create_date = models.DateTimeField(auto_now_add=True)

class Lot(models.Model):
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=1000)
    initial_rate = models.FloatField()
    category = models.ForeignKey(Category, on_delete=models.SET_DEFAULT, related_name="lotcategories", default=1)
    active = models.BooleanField(default=False) 
    create_date = models.DateTimeField(auto_now_add=True)
    picture = models.ImageField(blank=True, upload_to=_content_file_name, default="no-image.jpg") 
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lotusers")
    winner = models.IntegerField(default=0)

class Rate(models.Model):
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="ratelots", default=1)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rateusers")
    rate = models.FloatField()
    create_date = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="commentlots", default=1)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="commentusers")
    comment = models.CharField(max_length=1000)
    create_date = models.DateTimeField(auto_now_add=True)
    reply_to = models.IntegerField(default=0)

class Photo(models.Model):
    name = models.ImageField(blank=True, upload_to=_content_file_name, default="") 

class LotPhoto(models.Model):
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="imagelots", default=1)
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="imageusers", default=1)

class Watchlist(models.Model):
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="watchlistlots")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlistusers")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["lot", "user"],
                name = "watch_item"
            )
        ]