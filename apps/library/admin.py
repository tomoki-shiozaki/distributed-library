from django.contrib import admin

from apps.library.models import LoanHistory, ReservationHistory

# Register your models here.
admin.site.register(LoanHistory)
admin.site.register(ReservationHistory)
