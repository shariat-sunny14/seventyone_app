from django.contrib import admin
from . models import items, item_supplierdtl

# Register your models here.
admin.site.register(items)
admin.site.register(item_supplierdtl)