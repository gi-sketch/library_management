from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from books.models import Book
from transactions.models import IssueBook
from accounts.models import Profile


@login_required
def dashboard(request):

    profile = request.user.profile

    total_books = Book.objects.count()

    issued_books = IssueBook.objects.filter(
        returned=False
    ).count()

    available_books = sum(
        book.available_copies
        for book in Book.objects.all()
    )

    members = Profile.objects.filter(
        role='student'
    ).count()

    context = {
        'username': request.user.username,
        'role': profile.role,
        'total_books': total_books,
        'issued_books': issued_books,
        'available_books': available_books,
        'members': members,
    }

    return render(
        request,
        'dashboard/dashboard.html',
        context
    )

from django.shortcuts import render

def home(request):
    return render(
        request,
        'home.html'
    )