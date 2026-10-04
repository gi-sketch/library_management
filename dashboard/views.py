from decimal import Decimal
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

from books.models import Book
from transactions.models import IssueBook, Fine
from accounts.models import Profile
from transactions.views import sync_fines_for_student, sync_all_overdue_fines


@login_required
def dashboard(request):
    profile = request.user.profile
    role = profile.role

    total_books = Book.objects.count()
    issued_books_count = IssueBook.objects.filter(returned=False).count()
    available_books = sum(book.available_copies for book in Book.objects.all())
    members_count = Profile.objects.filter(role='student').count()

    context = {
        'username': request.user.username,
        'role': role,
        'total_books': total_books,
        'issued_books': issued_books_count,
        'available_books': available_books,
        'members': members_count,
    }

    if role == 'student':
        # Auto-sync overdue fines for logged-in student
        sync_fines_for_student(profile)
        student_unpaid_fines = Fine.objects.filter(member=profile, status='unpaid', amount__gt=0)
        unpaid_fine_total = student_unpaid_fines.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        unpaid_fines_count = student_unpaid_fines.count()

        context.update({
            'unpaid_fine_total': unpaid_fine_total,
            'unpaid_fines_count': unpaid_fines_count,
            'has_unpaid_fines': unpaid_fine_total > 0,
        })
    else:
        # Admin / Librarian: Auto-sync all overdue fines across the system
        sync_all_overdue_fines()
        all_unpaid = Fine.objects.filter(status='unpaid', amount__gt=0)
        all_paid = Fine.objects.filter(status='paid')

        total_unpaid_fines_count = all_unpaid.count()
        total_paid_fines_count = all_paid.count()
        total_collected_amount = all_paid.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        total_unpaid_amount = all_unpaid.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        context.update({
            'total_unpaid_fines_count': total_unpaid_fines_count,
            'total_paid_fines_count': total_paid_fines_count,
            'total_collected_amount': total_collected_amount,
            'total_unpaid_amount': total_unpaid_amount,
        })

    return render(
        request,
        'dashboard/dashboard.html',
        context
    )


def home(request):
    return render(
        request,
        'home.html'
    )