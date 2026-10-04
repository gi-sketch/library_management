from django.db import models

# Create your models here.
# books/models.py

class Category(models.Model):
    category_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.category_name

class Author(models.Model):
    author_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.author_name


class Book(models.Model):
    title = models.CharField(max_length=200)
    isbn = models.CharField(max_length=20, unique=True)

    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE
    )

    publisher = models.CharField(max_length=100)
    publication_year = models.PositiveIntegerField()

    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)

    book_cover = models.ImageField(
        upload_to='books/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):

        # For new books
        if not self.pk and not self.available_copies:
            self.available_copies = self.total_copies

        # Prevent available copies from exceeding total copies
        if self.available_copies > self.total_copies:
            self.available_copies = self.total_copies

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title