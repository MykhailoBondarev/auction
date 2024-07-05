from django.contrib import admin
from auctions.models import User, Category, Lot, Rate, Comment, Photo, LotPhoto
# Register your models here.

admin.site.register(User)
# admin.site.register(UserGroups)
admin.site.register(Category)
admin.site.register(Lot)
admin.site.register(Rate)
admin.site.register(Comment)
admin.site.register(Photo)
admin.site.register(LotPhoto)