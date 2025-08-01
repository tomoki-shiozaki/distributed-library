from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
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


class LoanReturnView(LoginRequiredMixin, IsGeneralMixin, View):
    def post(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        loan = get_object_or_404(LoanHistory, pk=pk, user=request.user)

        if loan.status == LoanHistory.Status.RETURNED:
            messages.warning(request, "この本はすでに返却されています。")
            return redirect("user_libraries:my_library")

        # 返却処理
        loan.mark_returned()

        loan.copy.status = Copy.Status.AVAILABLE
        loan.copy.save()

        messages.success(request, "返却が完了しました。")
        return redirect("user_libraries:my_library")


class ReservationCancelView(LoginRequiredMixin, IsGeneralMixin, View):
    def post(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        reservation = get_object_or_404(ReservationHistory, pk=pk, user=request.user)

        try:
            reservation.cancel()
        except ValidationError as e:
            messages.warning(request, str(e))
            return redirect("user_libraries:my_library")

        messages.success(request, "予約のキャンセルが完了しました。")
        return redirect("user_libraries:my_library")


class ReservationLoanView(LoginRequiredMixin, IsGeneralMixin, View):
    def post(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        reservation = get_object_or_404(ReservationHistory, pk=pk, user=request.user)

        try:
            loan = reservation.convert_to_loan()
        except ValidationError as e:
            messages.warning(request, str(e))
            return redirect("user_libraries:my_library")

        messages.success(request, "予約から貸出への変更が完了しました。")
        return redirect("user_libraries:my_library")
