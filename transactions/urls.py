from django.urls import path
from . import views

urlpatterns = [
    # Book Issue & Return Management
    path('issue/', views.issue_book, name='issue_book'),
    path('issued/', views.issued_books, name='issued_books'),
    path('return/<int:issue_id>/', views.return_book, name='return_book'),

    # Book Requests Management
    path('request/<int:book_id>/', views.request_book, name='request_book'),
    path('requests/', views.book_requests, name='book_requests'),
    path('approve/<int:id>/', views.approve_request, name='approve_request'),
    path('reject/<int:id>/', views.reject_request, name='reject_request'),

    # Fine Management & Views
    path('fines/', views.student_fines, name='student_fines'),
    path('payments/', views.librarian_payments, name='librarian_payments'),

    # Payment Gateway & Checkout
    path('pay/<int:fine_id>/', views.payment_page, name='payment_page'),
    path('create-payment/<int:fine_id>/', views.create_payment, name='create_payment'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('payment-success/<int:fine_id>/', views.payment_success, name='payment_success'),
    path('payment-failed/<int:fine_id>/', views.payment_failed, name='payment_failed'),
    path('receipt/<int:fine_id>/', views.payment_receipt, name='payment_receipt'),
]