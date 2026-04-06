"""
This module was created and tested with Python 3.11.
"""

from django.contrib import admin
from .models import VerificationRequest, ExtractedData, AuditLog

@admin.register(ExtractedData)
class ExtractedDataAdmin(admin.ModelAdmin):
    """
    Admin configuration for the ExtractedData model.
    """
    list_display = ('request', 'full_name', 'document_number', 'confidence_score')

class ExtractedDataInline(admin.StackedInline):
    """
    Inline display of extracted data within the verification request details.
    """
    model = ExtractedData
    can_delete = False
    verbose_name_plural = 'Datos Extraídos (OCR)'

@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    """
    Admin configuration for the VerificationRequest model.
    """
    list_display = ('id', 'user', 'document_type', 'status', 'created_at')
    list_filter = ('status', 'document_type', 'created_at')
    search_fields = ('user__username', 'id')
    inlines = [ExtractedDataInline]

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin configuration for the AuditLog model.
    """
    list_display = ('request', 'worker_node', 'execution_time', 'timestamp')
    list_filter = ('worker_node', 'timestamp')
    readonly_fields = ('timestamp',)
