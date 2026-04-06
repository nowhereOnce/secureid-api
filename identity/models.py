"""
This module was created and tested with Python 3.11.
"""

import uuid
from django.db import models
from django.contrib.auth.models import User

class VerificationRequest(models.Model):
    """
    Main model representing an identity verification request.

    Stores the uploaded document, optional selfie, and tracks the processing status.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('rejected', 'Rechazado'),
    ]

    DOC_TYPES = [
        ('ine', 'INE'),
        ('passport', 'Pasaporte'),
        ('id_card', 'Cédula Profesional'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verifications')
    document_type = models.CharField(max_length=20, choices=DOC_TYPES, default='ine')
    image = models.ImageField(upload_to='verifications/%Y/%m/%d/')
    face_image = models.ImageField(
        upload_to='faces/%Y/%m/%d/', 
        null=True, 
        blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_verification_mode = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        Return a string representation of the VerificationRequest.
        """
        return f"{self.user.username} - {self.document_type} ({self.status})"

class ExtractedData(models.Model):
    """
    Model to store the extracted data from the identity verification process.
    """
    
    request = models.OneToOneField(VerificationRequest, on_delete=models.CASCADE, related_name='extracted_data')

    # Universal Data
    full_name = models.CharField(max_length=255, blank=True, null=True)

    # Dinamic Data
    structured_data = models.JSONField(
        default=dict, 
        help_text="Datos específicos según el tipo de documento (CURP, Elector Key, etc.)",
        blank=True,
        null=True
    )
    
    # Metadata
    document_number = models.CharField(max_length=100, blank=True, null=True)
    confidence_score = models.FloatField(default=0.0)
    raw_json_response = models.JSONField(blank=True, null=True) # Storage for raw OCR output and any additional metadata

    def __str__(self):
        """
        Return a string representation of the ExtractedData.
        """
        return f"Data for {self.request.id}"

class AuditLog(models.Model):
    """
    Model to log the processing of each verification request.

    Includes execution time, worker node, and any errors encountered.
    """
    
    request = models.ForeignKey(VerificationRequest, on_delete=models.CASCADE, related_name='logs')
    worker_node = models.CharField(max_length=100)
    execution_time = models.FloatField(help_text="Tiempo en segundos")
    error_message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        Return a string representation of the AuditLog.
        """
        return f"Log {self.request.id} - {self.worker_node}"
