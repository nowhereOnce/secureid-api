from django.contrib import admin
from .models import VerificationRequest, ExtractedData, AuditLog

# Esto permite ver los datos extraídos directamente dentro de la solicitud de verificación
class ExtractedDataInline(admin.StackedInline):
    model = ExtractedData
    can_delete = False
    verbose_name_plural = 'Datos Extraídos (OCR)'

@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    # Columnas que verás en la lista principal
    list_display = ('id', 'user', 'document_type', 'status', 'created_at')
    
    # Filtros laterales para búsqueda rápida
    list_filter = ('status', 'document_type', 'created_at')
    
    # Buscador por usuario o ID
    search_fields = ('user__username', 'id')
    
    # Incluimos los datos del OCR en la misma vista
    inlines = [ExtractedDataInline]

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('request', 'worker_node', 'execution_time', 'timestamp')
    list_filter = ('worker_node', 'timestamp')
    readonly_fields = ('timestamp',)

@admin.register(ExtractedData)
class ExtractedDataAdmin(admin.ModelAdmin):
    list_display = ('request', 'full_name', 'document_number', 'confidence_score')