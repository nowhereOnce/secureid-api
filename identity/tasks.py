import time
import random
from celery import shared_task
from .models import VerificationRequest, ExtractedData, AuditLog

@shared_task(bind=True)
def process_ocr_task(self, request_id):
    """
    Simula el procesamiento pesado de OCR para una identificación.
    """
    start_time = time.time()
    
    # 1. Recuperar la solicitud de la base de datos
    try:
        request = VerificationRequest.objects.get(id=request_id)
        request.status = 'processing'
        request.save()
    except VerificationRequest.DoesNotExist:
        return f"Error: Request {request_id} no encontrada."

    # 2. Simular el trabajo pesado (Aquí es donde entraría tu GPU en el futuro)
    # Simulamos que el OCR tarda entre 5 y 10 segundos
    time.sleep(random.randint(5, 10))
    
    # 3. Guardar resultados simulados
    ExtractedData.objects.update_or_create(
        request=request,
        defaults={
            'full_name': 'ENRIQUE ALEJANDRO', # Tu nombre como prueba de éxito
            'document_number': 'CURP1234567890',
            'confidence_score': 0.98,
            'raw_json_response': {'engine': 'Tesseract-Simulated', 'status': 'success'}
        }
    )

    # 4. Actualizar estado y registrar auditoría
    request.status = 'completed'
    request.save()

    execution_time = time.time() - start_time
    AuditLog.objects.create(
        request=request,
        worker_node="Laptop-Mint-Worker", # Identificamos quién hizo el trabajo
        execution_time=execution_time
    )

    return f"Tarea {request_id} completada exitosamente por el nodo local."