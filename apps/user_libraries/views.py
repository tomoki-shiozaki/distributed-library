from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import TemplateView

from apps.catalog.models import Copy
from apps.core.mixins import IsGeneralMixin
from apps.library.models import LoanHistory, ReservationHistory


# Create your views here.
class MyLibraryView(LoginRequiredMixin, IsGeneralMixin, TemplateView):
    template_name = "user_libraries/my_library.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localdate()

        context["loans"] = LoanHistory.objects.filter(
            user=user, status=LoanHistory.Status.ON_LOAN
        ).select_related("copy", "copy__book", "copy__location")

        reservations = ReservationHistory.objects.filter(
            user=user, status=ReservationHistory.Status.RESERVED
        ).select_related("copy", "copy__book", "copy__location")

        for res in reservations:
            res.can_loan_now = (
                res.copy.status == Copy.Status.AVAILABLE
                and res.start_date <= today <= res.end_date
            )

        context["reservations"] = reservations
        return context
