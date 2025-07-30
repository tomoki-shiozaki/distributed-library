from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import TemplateView

from apps.core.mixins import IsGeneralMixin
from apps.library.models import LoanHistory, ReservationHistory


# Create your views here.
class MyLibraryView(LoginRequiredMixin, IsGeneralMixin, TemplateView):
    template_name = "user_libraries/my_library.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["loans"] = LoanHistory.objects.filter(
            user=user, status=LoanHistory.Status.ON_LOAN
        ).select_related("copy", "copy__book")
        context["reservations"] = ReservationHistory.objects.filter(
            user=user, status=ReservationHistory.Status.RESERVED
        ).select_related("copy", "copy__book")
        return context
