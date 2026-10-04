from django.urls import path
from . import views

urlpatterns = [

    path(
        'issue/',
        views.issue_book,
        name='issue_book'
    ),

    path(
        'issued/',
        views.issued_books,
        name='issued_books'
    ),

    path(
        'request/<int:book_id>/',
        views.request_book,
        name='request_book'
    ),

    path(
        'requests/',
        views.book_requests,
        name='book_requests'
    ),

    path(
        'approve/<int:id>/',
        views.approve_request,
        name='approve_request'
    ),

    path(
        'reject/<int:id>/',
        views.reject_request,
        name='reject_request'
    ),
]