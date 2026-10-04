from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Book
from .forms import BookForm


@login_required
def book_list(request):
    books = Book.objects.all()

    return render(
        request,
        'books/book_list.html',
        {'books': books}
    )


@login_required
def add_book(request):
    if request.user.profile.role not in ['admin', 'librarian']:
        return HttpResponseForbidden(
            "You do not have permission to add books."
        )

    if request.method == 'POST':
        form = BookForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            print("VALID")
            form.save()
            return redirect('book_list')
        else:
            print("ERRORS:", form.errors)

    else:
        form = BookForm()

    return render(
        request,
        'books/add_book.html',
        {'form': form}
    )

@login_required
def edit_book(request, id):

    book = Book.objects.get(id=id)

    if request.method == "POST":
        form = BookForm(
            request.POST,
            request.FILES,
            instance=book
        )

        if form.is_valid():
            print("EDIT VALID")
            print(form.cleaned_data)

            book = form.save()

            print("Saved:")
            print(book.title)
            print(book.author)
            print(book.category)
            print(book.publisher)
            print(book.total_copies)
            print(book.available_copies)

            return redirect('book_list')
        else:
            print(form.errors)

    else:
        form = BookForm(instance=book)

    return render(
        request,
        'books/edit_book.html',
        {
            'form': form,
            'book': book
        }
    )

@login_required
def delete_book(request, id):
    book = get_object_or_404(Book, id=id)

    if request.method == 'POST':
        book.delete()
        return redirect('book_list')

    return render(
        request,
        'books/delete_book.html',
        {'book': book}
    )