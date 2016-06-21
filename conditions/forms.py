from django import forms
from django.forms.utils import ErrorList


class DivErrorList(ErrorList):

    def __str__(self):
        return self.as_divs()

    def as_divs(self):
        if not self:
            return ''
        return '<div class="control-label">%s</div>' % ''.join(['<div class="error">%s</div>' % e for e in self])


class SearchForm(forms.Form):

    q = forms.CharField(label='',
                        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search'}))

    def clean_q(self):
        data = self.cleaned_data['q'].strip()
        data = ' '.join(data.split())

        return data
