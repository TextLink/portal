from django import forms
from portal.models import *


class DocumentForm(forms.ModelForm):
    class Meta:
        model = uploaded_files
        fields = ('ann_file', 'raw_file',  )
        annotationFile = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple':True}))
        rawFile = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

