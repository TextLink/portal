from django import forms
from portal.models import *


class DocumentForm(forms.ModelForm):
    class Meta:
        model = uploaded_files
        fields = ('ann_file', 'raw_file',  )
        annotationFile = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple':True}))
        rawFile = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))


class AnnotationForm(forms.ModelForm):
    class Meta:
        model = pdtbAnnotation
        fields = ('type', 'conn', 'connBeg', 'connEnd', 'connBeg2', 'connEnd2', 'sense1', 'sense2', 'arg1', 'arg1Beg', 'arg1End', 'arg1Beg2', 'arg1End2', 'arg2', 'arg2Beg', 'arg2End', 'arg2Beg2', 'arg2End2', 'arg2End2')

