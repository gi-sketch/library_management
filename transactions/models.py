from django.db import models
from books.models import Book
from accounts.models import Profile
from django.contrib.auth.models import User
from django.conf import settings
from decimal import Decimal
from datetime import date


class IssueBook(models.Model):
    member = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE
    )

    issue_date = models.DateField(
        auto_now_add=True
    )

    due_date = models.DateField()

    return_date = models.DateField(
        null=True,
        blank=True
    )

    fine = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00')
    )

    returned = models.BooleanField(
        default=False
    )

    def calculate_overdue_days(self):
        """Calculates overdue days based on return_date or current date."""
        target_date = self.return_date if self.returned and self.return_date else date.today()
        if target_date > self.due_date:
            return (target_date - self.due_date).days
        return 0

    def calculate_fine_amount(self, daily_rate=None):
        """Calculates fine amount using configured daily rate."""
        if daily_rate is None:
            daily_rate = getattr(settings, 'DAILY_FINE_RATE', Decimal('5.00'))
        overdue_days = self.calculate_overdue_days()
        return Decimal(overdue_days) * Decimal(daily_rate)

    def __str__(self):
        return f"{self.member.user.username} - {self.book.title}"


class BookRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    request_date = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.student.username} - {self.book.title}"


class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.message


class Fine(models.Model):
    STATUS_CHOICES = (
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
    )

    member = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='fines'
    )

    issue_book = models.OneToOneField(
        IssueBook,
        on_delete=models.CASCADE,
        related_name='fine_record'
    )

    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00')
    )

    overdue_days = models.PositiveIntegerField(
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='unpaid'
    )

    razorpay_order_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Fine: {self.member.user.username} - {self.issue_book.book.title} (₹{self.amount}) [{self.status}]"