from django.contrib import admin

from apps.catalog.models import Book, Copy, StorageLocation

# Register your models here.
admin.site.register(Book)
admin.site.register(StorageLocation)
admin.site.register(Copy)
