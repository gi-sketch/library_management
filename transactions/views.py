from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from datetime import date, timedelta
from .forms import IssueBookForm
from .models import IssueBook, BookRequest
from books.models import Book


# ==========================================
# MANUAL ISSUE BOOK
# ==========================================

@login_required
def issue_book(request):

    if request.user.profile.role not in [
        'admin',
        'librarian'
    ]:
        return HttpResponseForbidden(
            "You do not have permission."
        )

    if request.method == 'POST':

        form = IssueBookForm(
            request.POST
        )

        if form.is_valid():

            issue = form.save(
                commit=False
            )

            book = issue.book

            if book.available_copies > 0:

                book.available_copies -= 1
                book.save()

                issue.save()

                return redirect(
                    'issued_books'
                )

    else:
        form = IssueBookForm()

    return render(
        request,
        'transactions/issue_book.html',
        {
            'form': form
        }
    )


# ==========================================
# VIEW ISSUED BOOKS
# ==========================================

@login_required
def issued_books(request):

    if request.user.profile.role in [
        'admin',
        'librarian'
    ]:
        issues = IssueBook.objects.all()

    else:
        issues = IssueBook.objects.filter(
            user=request.user
        )

    return render(
        request,
        'transactions/issued_books.html',
        {
            'issues': issues
        }
    )


# ==========================================
# STUDENT REQUEST BOOK
# ==========================================

@login_required
def request_book(
    request,
    book_id
):

    if request.user.profile.role != 'student':
        return HttpResponseForbidden(
            "Only students can request books."
        )

    book = get_object_or_404(
        Book,
        id=book_id
    )

    if book.available_copies <= 0:
        return redirect(
            'book_list'
        )

    already_requested = (
        BookRequest.objects.filter(
            student=request.user,
            book=book,
            status='pending'
        ).exists()
    )

    if not already_requested:

        BookRequest.objects.create(
            student=request.user,
            book=book
        )

    return redirect(
        'book_list'
    )


# ==========================================
# LIBRARIAN VIEW REQUESTS
# ==========================================

@login_required
def book_requests(request):

    if request.user.profile.role not in [
        'admin',
        'librarian'
    ]:
        return HttpResponseForbidden(
            "Permission denied"
        )

    requests = (
        BookRequest.objects.all()
        .order_by('-request_date')
    )

    return render(
        request,
        'transactions/book_requests.html',
        {
            'requests': requests
        }
    )


# ==========================================
# APPROVE REQUEST
# ==========================================

@login_required
def approve_request(request, id):

    if request.user.profile.role not in [
        'admin',
        'librarian'
    ]:
        return HttpResponseForbidden()

    req = get_object_or_404(
        BookRequest,
        id=id
    )

    if req.status == 'pending':

        if req.book.available_copies > 0:

            # move request to issued books
            IssueBook.objects.create(
                member=req.student.profile,
                book=req.book,
                due_date=date.today() + timedelta(days=14)
            )

            # decrease available copies
            req.book.available_copies -= 1
            req.book.save()

            # mark request approved
            req.status = 'approved'
            req.save()

    return redirect(
        'book_requests'
    )


# ==========================================
# REJECT REQUEST
# ==========================================

@login_required
def reject_request(
    request,
    id
):

    if request.user.profile.role not in [
        'admin',
        'librarian'
    ]:
        return HttpResponseForbidden()

    req = get_object_or_404(
        BookRequest,
        id=id
    )

    req.status = 'rejected'
    req.save()

    return redirect(
        'book_requests'
    )