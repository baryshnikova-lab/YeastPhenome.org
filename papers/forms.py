from django.forms import ModelForm, Textarea
from .models import Paper


class PaperModelForm(ModelForm):

    class Meta:
        model = Paper
        fields = ('__all__')
        widgets = {
            'data_abstract': Textarea(attrs={'cols': 85, 'rows': 3}),
        }
