from django.contrib import admin
from .models import IssueBook, BookRequest, Fine, Notification


@admin.register(IssueBook)
class IssueBookAdmin(admin.ModelAdmin):
    list_display = (
        'member',
        'book',
        'issue_date',
        'due_date',
        'return_date',
        'returned',
        'fine'
    )
    list_filter = (
        'returned',
        'issue_date',
        'due_date'
    )
    search_fields = (
        'member__user__username',
        'book__title',
        'book__isbn'
    )


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = (
        'member',
        'issue_book',
        'amount',
        'overdue_days',
        'status',
        'payment_reference',
        'paid_at',
        'created_at'
    )
    list_filter = (
        'status',
        'created_at',
        'paid_at'
    )
    search_fields = (
        'member__user__username',
        'issue_book__book__title',
        'payment_reference',
        'razorpay_order_id'
    )
    readonly_fields = (
        'created_at',
    )


@admin.register(BookRequest)
class BookRequestAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'book',
        'status',
        'request_date'
    )
    list_filter = (
        'status',
        'request_date'
    )
    search_fields = (
        'student__username',
        'book__title'
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'message',
        'is_read',
        'created_at'
    )
    list_filter = (
        'is_read',
        'created_at'
    )