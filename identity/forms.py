from django import forms
from .models import VerificationRequest

class IdentityUploadForm(forms.ModelForm):
    class Meta:
        model = VerificationRequest
        fields = ['document_type', 'image']
