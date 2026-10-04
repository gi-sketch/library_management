from django import forms
from .models import IssueBook


class IssueBookForm(forms.ModelForm):

    class Meta:
        model = IssueBook
        fields = [
            'member',
            'book',
            'due_date'
        ]

        widgets = {
            'due_date': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-input'
            })