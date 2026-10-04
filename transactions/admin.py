from django.contrib import admin
from .models import IssueBook, BookRequest


@admin.register(IssueBook)
class IssueBookAdmin(admin.ModelAdmin):
    list_display = (
        'member',
        'book',
        'issue_date',
        'due_date',
        'returned',
        'fine'
    )

    list_filter = (
        'returned',
        'issue_date'
    )

    search_fields = (
        'member__user__username',
        'book__title'
    )

admin.site.register(BookRequest)