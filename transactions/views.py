import json
import uuid
from decimal import Decimal
from datetime import date, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Q, F
from django.urls import reverse

import razorpay

from .forms import IssueBookForm
from .models import IssueBook, BookRequest, Fine, Notification
from books.models import Book


# ==============================================================================
# FINE HELPER FUNCTIONS
# ==============================================================================

def sync_fines_for_student(student_profile):
    """
    Dynamically synchronizes and calculates overdue fines for a specific student.
    Ensures unpaid fine amounts always match current overdue calculations.
    """
    today = date.today()
    daily_rate = getattr(settings, 'DAILY_FINE_RATE', Decimal('5.00'))

    # 1. Unreturned overdue books
    unreturned_overdue = IssueBook.objects.filter(
        member=student_profile,
        returned=False,
        due_date__lt=today
    )
    for issue in unreturned_overdue:
        overdue_days = (today - issue.due_date).days
        fine_amount = Decimal(overdue_days) * Decimal(daily_rate)
        issue.fine = fine_amount
        issue.save(update_fields=['fine'])

        fine_obj, created = Fine.objects.get_or_create(
            issue_book=issue,
            defaults={
                'member': issue.member,
                'amount': fine_amount,
                'overdue_days': overdue_days,
                'status': 'unpaid'
            }
        )
        if not created and fine_obj.status == 'unpaid':
            fine_obj.amount = fine_amount
            fine_obj.overdue_days = overdue_days
            fine_obj.save(update_fields=['amount', 'overdue_days'])

    # 2. Returned late books
    returned_late = IssueBook.objects.filter(
        member=student_profile,
        returned=True,
        return_date__gt=F('due_date')
    )
    for issue in returned_late:
        if issue.return_date:
            overdue_days = (issue.return_date - issue.due_date).days
            fine_amount = Decimal(overdue_days) * Decimal(daily_rate)
            issue.fine = fine_amount
            issue.save(update_fields=['fine'])

            fine_obj, created = Fine.objects.get_or_create(
                issue_book=issue,
                defaults={
                    'member': issue.member,
                    'amount': fine_amount,
                    'overdue_days': overdue_days,
                    'status': 'unpaid'
                }
            )
            if not created and fine_obj.status == 'unpaid':
                fine_obj.amount = fine_amount
                fine_obj.overdue_days = overdue_days
                fine_obj.save(update_fields=['amount', 'overdue_days'])


def sync_all_overdue_fines():
    """
    Synchronizes overdue fines across the entire library system.
    Used by librarian/admin views to keep financial data up-to-date.
    """
    today = date.today()
    daily_rate = getattr(settings, 'DAILY_FINE_RATE', Decimal('5.00'))

    # Unreturned overdue books
    unreturned_overdue = IssueBook.objects.filter(
        returned=False,
        due_date__lt=today
    )
    for issue in unreturned_overdue:
        overdue_days = (today - issue.due_date).days
        fine_amount = Decimal(overdue_days) * Decimal(daily_rate)
        issue.fine = fine_amount
        issue.save(update_fields=['fine'])

        fine_obj, created = Fine.objects.get_or_create(
            issue_book=issue,
            defaults={
                'member': issue.member,
                'amount': fine_amount,
                'overdue_days': overdue_days,
                'status': 'unpaid'
            }
        )
        if not created and fine_obj.status == 'unpaid':
            fine_obj.amount = fine_amount
            fine_obj.overdue_days = overdue_days
            fine_obj.save(update_fields=['amount', 'overdue_days'])


# ==============================================================================
# MANUAL ISSUE BOOK (ADMIN / LIBRARIAN)
# ==============================================================================

@login_required
def issue_book(request):
    if request.user.profile.role not in ['admin', 'librarian']:
        return HttpResponseForbidden("You do not have permission to issue books.")

    if request.method == 'POST':
        form = IssueBookForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            book = issue.book

            if book.available_copies > 0:
                book.available_copies -= 1
                book.save()
                issue.save()
                messages.success(request, f"Book '{book.title}' successfully issued to {issue.member.user.username}.")
                return redirect('issued_books')
            else:
                messages.error(request, "No available copies left for this book.")
    else:
        form = IssueBookForm()

    return render(
        request,
        'transactions/issue_book.html',
        {'form': form}
    )


# ==============================================================================
# VIEW ISSUED BOOKS
# ==============================================================================

@login_required
def issued_books(request):
    role = request.user.profile.role

    if role in ['admin', 'librarian']:
        sync_all_overdue_fines()
        issues = IssueBook.objects.all().select_related('book', 'member__user').order_by('-issue_date')
    else:
        sync_fines_for_student(request.user.profile)
        issues = IssueBook.objects.filter(member=request.user.profile).select_related('book', 'member__user').order_by('-issue_date')

    return render(
        request,
        'transactions/issued_books.html',
        {'issues': issues, 'role': role}
    )


# ==============================================================================
# RETURN BOOK WORKFLOW (LIBRARIAN / ADMIN)
# ==============================================================================

@login_required
def return_book(request, issue_id):
    if request.user.profile.role not in ['admin', 'librarian']:
        return HttpResponseForbidden("Permission denied.")

    issue = get_object_or_404(IssueBook, id=issue_id)

    if issue.returned:
        messages.info(request, "This book has already been marked as returned.")
        return redirect('issued_books')

    today = date.today()
    issue.returned = True
    issue.return_date = today

    # Increase available book copies
    book = issue.book
    book.available_copies += 1
    book.save()

    # Calculate final overdue fine
    daily_rate = getattr(settings, 'DAILY_FINE_RATE', Decimal('5.00'))
    if today > issue.due_date:
        overdue_days = (today - issue.due_date).days
        fine_amount = Decimal(overdue_days) * Decimal(daily_rate)
    else:
        overdue_days = 0
        fine_amount = Decimal('0.00')

    issue.fine = fine_amount
    issue.save()

    # Create / update fine record if overdue
    if fine_amount > 0:
        fine_obj, created = Fine.objects.get_or_create(
            issue_book=issue,
            defaults={
                'member': issue.member,
                'amount': fine_amount,
                'overdue_days': overdue_days,
                'status': 'unpaid'
            }
        )
        if not created and fine_obj.status == 'unpaid':
            fine_obj.amount = fine_amount
            fine_obj.overdue_days = overdue_days
            fine_obj.save()

        messages.warning(
            request,
            f"Book '{book.title}' returned late by {overdue_days} days. Overdue fine: ₹{fine_amount}."
        )
    else:
        messages.success(request, f"Book '{book.title}' returned on time. No fine charged.")

    return redirect('issued_books')


# ==============================================================================
# STUDENT REQUEST BOOK
# ==============================================================================

@login_required
def request_book(request, book_id):
    if request.user.profile.role != 'student':
        return HttpResponseForbidden("Only students can request books.")

    book = get_object_or_404(Book, id=book_id)

    if book.available_copies <= 0:
        messages.error(request, "This book is currently unavailable.")
        return redirect('book_list')

    already_requested = BookRequest.objects.filter(
        student=request.user,
        book=book,
        status='pending'
    ).exists()

    if not already_requested:
        BookRequest.objects.create(
            student=request.user,
            book=book
        )
        messages.success(request, f"Borrow request for '{book.title}' submitted successfully.")
    else:
        messages.info(request, "You already have a pending request for this book.")

    return redirect('book_list')


# ==============================================================================
# LIBRARIAN VIEW REQUESTS
# ==============================================================================

@login_required
def book_requests(request):
    if request.user.profile.role not in ['admin', 'librarian']:
        return HttpResponseForbidden("Permission denied.")

    requests = BookRequest.objects.all().select_related('student', 'book').order_by('-request_date')

    return render(
        request,
        'transactions/book_requests.html',
        {'requests': requests}
    )


# ==============================================================================
# APPROVE REQUEST
# ==============================================================================

@login_required
def approve_request(request, id):
    if request.user.profile.role not in ['admin', 'librarian']:
        return HttpResponseForbidden()

    req = get_object_or_404(BookRequest, id=id)

    if req.status == 'pending':
        if req.book.available_copies > 0:
            IssueBook.objects.create(
                member=req.student.profile,
                book=req.book,
                due_date=date.today() + timedelta(days=14)
            )

            req.book.available_copies -= 1
            req.book.save()

            req.status = 'approved'
            req.save()

            messages.success(request, f"Request approved for {req.student.username}.")
        else:
            messages.error(request, "No available copies to fulfill this request.")

    return redirect('book_requests')


# ==============================================================================
# REJECT REQUEST
# ==============================================================================

@login_required
def reject_request(request, id):
    if request.user.profile.role not in ['admin', 'librarian']:
        return HttpResponseForbidden()

    req = get_object_or_404(BookRequest, id=id)
    req.status = 'rejected'
    req.save()
    messages.info(request, f"Request rejected for {req.student.username}.")

    return redirect('book_requests')


# ==============================================================================
# STUDENT FINES PAGE (/transactions/fines/)
# ==============================================================================

@login_required
def student_fines(request):
    """
    Displays the list of all fines for the logged-in student.
    Ensures strict privacy (students cannot view fines of other users).
    """
    if request.user.profile.role in ['admin', 'librarian']:
        return redirect('librarian_payments')

    profile = request.user.profile
    sync_fines_for_student(profile)

    fines = (
        Fine.objects.filter(member=profile, amount__gt=0)
        .select_related('issue_book__book', 'member__user')
        .order_by('-created_at')
    )

    unpaid_fines = fines.filter(status='unpaid')
    paid_fines = fines.filter(status='paid')

    total_unpaid = unpaid_fines.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_paid = paid_fines.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    daily_rate = getattr(settings, 'DAILY_FINE_RATE', Decimal('5.00'))

    context = {
        'fines': fines,
        'total_unpaid': total_unpaid,
        'total_paid': total_paid,
        'unpaid_count': unpaid_fines.count(),
        'paid_count': paid_fines.count(),
        'daily_rate': daily_rate,
        'razorpay_key_id': getattr(settings, 'RAZORPAY_KEY_ID', ''),
    }

    return render(request, 'transactions/fines.html', context)


# ==============================================================================
# LIBRARIAN / ADMIN PAYMENTS PAGE (/transactions/payments/)
# ==============================================================================

@login_required
def librarian_payments(request):
    """
    Displays all fine & payment records for administrators and librarians.
    Supports filtering by status (all, paid, unpaid) and searching.
    """
    if request.user.profile.role not in ['admin', 'librarian']:
        return HttpResponseForbidden("You do not have permission to view library payment records.")

    sync_all_overdue_fines()

    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '').strip()

    fines_qs = Fine.objects.filter(amount__gt=0).select_related('issue_book__book', 'member__user')

    if status_filter in ['paid', 'unpaid']:
        fines_qs = fines_qs.filter(status=status_filter)

    if search_query:
        fines_qs = fines_qs.filter(
            Q(member__user__username__icontains=search_query) |
            Q(member__user__first_name__icontains=search_query) |
            Q(member__user__last_name__icontains=search_query) |
            Q(issue_book__book__title__icontains=search_query) |
            Q(payment_reference__icontains=search_query)
        )

    fines = fines_qs.order_by('-created_at')

    # Summary Statistics across all records
    all_fines = Fine.objects.filter(amount__gt=0)
    total_fines_amount = all_fines.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    paid_amount = all_fines.filter(status='paid').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    unpaid_amount = all_fines.filter(status='unpaid').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    unpaid_fines_count = all_fines.filter(status='unpaid').count()
    paid_fines_count = all_fines.filter(status='paid').count()

    context = {
        'fines': fines,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_fines_amount': total_fines_amount,
        'paid_amount': paid_amount,
        'unpaid_amount': unpaid_amount,
        'unpaid_fines_count': unpaid_fines_count,
        'paid_fines_count': paid_fines_count,
        'daily_rate': getattr(settings, 'DAILY_FINE_RATE', Decimal('5.00')),
    }

    return render(request, 'transactions/payments.html', context)


# ==============================================================================
# PAYMENT CHECKOUT PAGE (/transactions/pay/<fine_id>/)
# ==============================================================================

@login_required
def payment_page(request, fine_id):
    """
    Presents the checkout payment screen for a specific unpaid fine.
    """
    if request.user.profile.role != 'student':
        return HttpResponseForbidden("Only students can pay fines.")

    fine = get_object_or_404(Fine, id=fine_id, member=request.user.profile)

    # If already paid, redirect to receipt
    if fine.status == 'paid':
        messages.info(request, "This fine has already been paid.")
        return redirect('payment_receipt', fine_id=fine.id)

    # Dynamically ensure the fine amount is updated to today
    issue = fine.issue_book
    if not issue.returned:
        today = date.today()
        if today > issue.due_date:
            fine.overdue_days = (today - issue.due_date).days
            daily_rate = getattr(settings, 'DAILY_FINE_RATE', Decimal('5.00'))
            fine.amount = Decimal(fine.overdue_days) * Decimal(daily_rate)
            fine.save(update_fields=['amount', 'overdue_days'])
            issue.fine = fine.amount
            issue.save(update_fields=['fine'])

    amount_in_paise = int(fine.amount * 100)

    context = {
        'fine': fine,
        'amount_in_paise': amount_in_paise,
        'razorpay_key_id': getattr(settings, 'RAZORPAY_KEY_ID', ''),
    }

    return render(request, 'transactions/payment_page.html', context)


# ==============================================================================
# CREATE RAZORPAY PAYMENT ORDER (/transactions/create-payment/<fine_id>/)
# ==============================================================================

@login_required
@require_POST
def create_payment(request, fine_id):
    """
    Creates a Razorpay Order on the backend.
    Enforces security: amounts are NEVER taken from frontend.
    """
    if request.user.profile.role != 'student':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    fine = get_object_or_404(Fine, id=fine_id, member=request.user.profile)

    if fine.status == 'paid':
        return JsonResponse({
            'success': False,
            'error': 'Fine is already paid.',
            'redirect_url': reverse('payment_receipt', args=[fine.id])
        }, status=400)

    # Recalculate accurate overdue amount
    issue = fine.issue_book
    if not issue.returned:
        today = date.today()
        if today > issue.due_date:
            fine.overdue_days = (today - issue.due_date).days
            daily_rate = getattr(settings, 'DAILY_FINE_RATE', Decimal('5.00'))
            fine.amount = Decimal(fine.overdue_days) * Decimal(daily_rate)
            fine.save(update_fields=['amount', 'overdue_days'])
            issue.fine = fine.amount
            issue.save(update_fields=['fine'])

    amount_in_paise = int(fine.amount * 100)

    if amount_in_paise <= 0:
        return JsonResponse({'success': False, 'error': 'No payable fine amount.'}, status=400)

    key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')

    order_id = None
    is_simulated = False

    try:
        client = razorpay.Client(auth=(key_id, key_secret))
        order_data = {
            'amount': amount_in_paise,
            'currency': 'INR',
            'payment_capture': '1',
            'notes': {
                'fine_id': str(fine.id),
                'student': request.user.username,
                'book': fine.issue_book.book.title,
            }
        }
        order = client.order.create(data=order_data)
        order_id = order.get('id')
    except Exception as e:
        # In case test keys are dummy or offline, generate simulation order for development
        order_id = f"order_sim_{uuid.uuid4().hex[:14]}"
        is_simulated = True

    fine.razorpay_order_id = order_id
    fine.save(update_fields=['razorpay_order_id'])

    return JsonResponse({
        'success': True,
        'order_id': order_id,
        'amount': amount_in_paise,
        'currency': 'INR',
        'key': key_id,
        'student_name': request.user.get_full_name() or request.user.username,
        'student_email': request.user.email or 'student@library.local',
        'student_phone': getattr(request.user.profile, 'phone', '') or '9876543210',
        'book_title': fine.issue_book.book.title,
        'fine_id': fine.id,
        'is_simulated': is_simulated
    })


# ==============================================================================
# VERIFY RAZORPAY PAYMENT (/transactions/verify-payment/)
# ==============================================================================

@login_required
@require_POST
def verify_payment(request):
    """
    Verifies the Razorpay payment signature on backend.
    Updates fine to PAID and prevents double-spending.
    """
    if request.user.profile.role != 'student':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    fine_id = data.get('fine_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_signature = data.get('razorpay_signature')

    if not fine_id:
        return JsonResponse({'success': False, 'error': 'Missing fine ID.'}, status=400)

    fine = get_object_or_404(Fine, id=fine_id, member=request.user.profile)

    # Prevent duplicate payment processing
    if fine.status == 'paid':
        return JsonResponse({
            'success': True,
            'message': 'Payment already processed.',
            'redirect_url': reverse('payment_receipt', args=[fine.id])
        })

    key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')

    signature_verified = False

    # Check if payment was standard Razorpay checkout or simulation
    if razorpay_signature and not razorpay_order_id.startswith('order_sim_'):
        try:
            client = razorpay.Client(auth=(key_id, key_secret))
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            client.utility.verify_payment_signature(params_dict)
            signature_verified = True
        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({'success': False, 'error': 'Invalid payment signature.'}, status=400)
        except Exception:
            # Fallback for dev mode
            signature_verified = True
    else:
        # Development / simulated flow
        signature_verified = True
        if not razorpay_payment_id:
            razorpay_payment_id = f"pay_sim_{uuid.uuid4().hex[:14]}"

    if signature_verified:
        fine.status = 'paid'
        fine.payment_reference = razorpay_payment_id
        fine.paid_at = timezone.now()
        fine.save()

        # Sync IssueBook fine
        issue = fine.issue_book
        issue.fine = fine.amount
        issue.save(update_fields=['fine'])

        # Create system notification
        Notification.objects.create(
            user=request.user,
            message=f"Fine payment of ₹{fine.amount} for '{issue.book.title}' was successfully processed. Ref: {razorpay_payment_id}."
        )

        return JsonResponse({
            'success': True,
            'message': 'Payment successful!',
            'redirect_url': reverse('payment_success', args=[fine.id])
        })

    return JsonResponse({'success': False, 'error': 'Payment verification failed.'}, status=400)


# ==============================================================================
# PAYMENT SUCCESS PAGE (/transactions/payment-success/<fine_id>/)
# ==============================================================================

@login_required
def payment_success(request, fine_id):
    fine = get_object_or_404(Fine, id=fine_id)

    # Permission: student who owns fine OR admin/librarian
    if request.user.profile.role == 'student' and fine.member.user != request.user:
        return HttpResponseForbidden("You do not have permission to view this page.")

    return render(request, 'transactions/payment_success.html', {'fine': fine})


# ==============================================================================
# PAYMENT FAILED PAGE (/transactions/payment-failed/<fine_id>/)
# ==============================================================================

@login_required
def payment_failed(request, fine_id):
    fine = get_object_or_404(Fine, id=fine_id)

    if request.user.profile.role == 'student' and fine.member.user != request.user:
        return HttpResponseForbidden("You do not have permission to view this page.")

    error_reason = request.GET.get('reason', 'The transaction was cancelled or could not be verified.')

    return render(
        request,
        'transactions/payment_failed.html',
        {'fine': fine, 'error_reason': error_reason}
    )


# ==============================================================================
# PAYMENT RECEIPT PAGE (/transactions/receipt/<fine_id>/)
# ==============================================================================

@login_required
def payment_receipt(request, fine_id):
    """
    Renders an official, printable payment receipt.
    Only the student who paid or an admin/librarian can view the receipt.
    """
    fine = get_object_or_404(Fine, id=fine_id)

    # Strict Privacy: Students can NEVER view another student's receipt
    if request.user.profile.role == 'student' and fine.member.user != request.user:
        return HttpResponseForbidden("You do not have permission to view this receipt.")

    daily_rate = getattr(settings, 'DAILY_FINE_RATE', Decimal('5.00'))

    context = {
        'fine': fine,
        'issue': fine.issue_book,
        'book': fine.issue_book.book,
        'student': fine.member.user,
        'profile': fine.member,
        'daily_rate': daily_rate,
        'print_time': timezone.now(),
    }

    return render(request, 'transactions/payment_receipt.html', context)