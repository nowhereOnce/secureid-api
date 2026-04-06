"""
This module was created and tested with Python 3.11.
"""

from django import forms
from .models import VerificationRequest

class IdentityUploadForm(forms.ModelForm):
    """
    Form for uploading documents for identity verification.
    """
    class Meta:
        """
        Metadata for the IdentityUploadForm.
        """
        model = VerificationRequest
        fields = ['document_type', 'image']
