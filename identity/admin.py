from django.contrib import admin
from .models import VerificationRequest, ExtractedData, AuditLog

# This file registers the models in the Django admin interface, 
# allowing administrators to view and manage verification requests, 
# extracted data, and audit logs. It also includes an inline display 
# of extracted data within the verification request details for easy access.

class ExtractedDataInline(admin.StackedInline):
    model = ExtractedData
    can_delete = False
    verbose_name_plural = 'Datos Extraídos (OCR)'

@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'document_type', 'status', 'created_at')
    list_filter = ('status', 'document_type', 'created_at')
    search_fields = ('user__username', 'id')
    inlines = [ExtractedDataInline] # Allows viewing extracted data directly from the verification request admin page

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('request', 'worker_node', 'execution_time', 'timestamp')
    list_filter = ('worker_node', 'timestamp')
    readonly_fields = ('timestamp',)

@admin.register(ExtractedData)
class ExtractedDataAdmin(admin.ModelAdmin):
    list_display = ('request', 'full_name', 'document_number', 'confidence_score')