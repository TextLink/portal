from django import forms
from portal.models import Documents


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Documents
        fields = ('description', 'document', )
