from apps.library.models import LoanHistory, ReservationHistory


def is_overlap(start1, end1, start2, end2):
    return start1 < end2 and start2 < end1


def is_copy_available(copy, start, end, book):
    # 貸出との重複確認
    loans = LoanHistory.objects.filter(copy=copy, status=LoanHistory.Status.ON_LOAN)
    for loan in loans:
        if is_overlap(loan.loan_date, loan.due_date, start, end):
            return False

    # 予約との重複確認
    reservations = ReservationHistory.objects.filter(
        book=book, status=ReservationHistory.Status.RESERVED
    )
    for reservation in reservations:
        if is_overlap(reservation.start_datetime, reservation.end_datetime, start, end):
            return False

    return True


def book_has_available_copy(book, start, end):
    copies = book.copies.all()
    for copy in copies:
        if is_copy_available(copy, start, end, book):
            return True
    return False
