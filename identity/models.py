import uuid
from django.db import models
from django.contrib.auth.models import User

class VerificationRequest(models.Model):
    """Entidad maestra para el seguimiento de solicitudes de identidad."""
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.document_type} ({self.status})"

class ExtractedData(models.Model):
    """Resultados detallados del OCR procesado por los Workers."""
    request = models.OneToOneField(VerificationRequest, on_delete=models.CASCADE, related_name='extracted_data')
    full_name = models.CharField(max_length=255, blank=True, null=True)
    document_number = models.CharField(max_length=100, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    
    confidence_score = models.FloatField(default=0.0)
    raw_json_response = models.JSONField(blank=True, null=True) # Para guardar la respuesta bruta del motor

    def __str__(self):
        return f"Data for {self.request.id}"

class AuditLog(models.Model):
    """Registro de trazabilidad para el sistema distribuido."""
    request = models.ForeignKey(VerificationRequest, on_delete=models.CASCADE, related_name='logs')
    worker_node = models.CharField(max_length=100) # Ej: "Laptop-Mint" o "Desktop-Win-GPU"
    execution_time = models.FloatField(help_text="Tiempo en segundos")
    error_message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log {self.request.id} - {self.worker_node}"