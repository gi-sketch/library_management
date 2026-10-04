from django import forms
from .models import Book, Author, Category


class BookForm(forms.ModelForm):

    author_name = forms.CharField(
        label='Author',
        max_length=100
    )

    category_name = forms.CharField(
        label='Category',
        max_length=100
    )

    class Meta:
        model = Book
        exclude = [
            'author',
            'category',
            'created_at'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Edit mode
        if self.instance and self.instance.pk:
            self.fields['author_name'].initial = \
                self.instance.author.author_name

            self.fields['category_name'].initial = \
                self.instance.category.category_name

            # Don't allow editing total copies
            self.fields['total_copies'].disabled = True

        # Add mode
        else:
            # Don't show available copies while adding
            self.fields.pop('available_copies')

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-input'
            })

    def save(self, commit=True):

        author, _ = Author.objects.get_or_create(
            author_name=self.cleaned_data['author_name']
        )

        category, _ = Category.objects.get_or_create(
            category_name=self.cleaned_data['category_name']
        )

        book = super().save(commit=False)

        book.author = author
        book.category = category

        # For new books
        if not book.pk:
            book.available_copies = book.total_copies

        if commit:
            book.save()

        return book