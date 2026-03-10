import easyocr
import os
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
    worker_node = os.environ.get('WORKER_NAME', "Unknown-Node")
    
    # 1. Recuperar la solicitud de la base de datos
    try:
        request = VerificationRequest.objects.get(id=request_id)
        request.status = 'processing'
        request.save()

        #GPU intensive task
        reader = easyocr.Reader(['es'], gpu=True)
        image_path = request.image.path
        result = reader.readtext(image_path, detail=0)
        full_text = " ".join(result)

        # Save
        ExtractedData.objects.update_or_create(
            request=request,
            defaults={
                'full_name': result[0] if len(result) > 0 else "No detectado",
                'document_number': "Procesado por IA",
                'confidence_score': 0.95,
                'raw_json_response': {'detected_text': result}
            }
        )

        request.status = 'completed'
        request.save()

    except Exception as e:
        request.status  = 'failed'
        request.save()
        AuditLog.objects.create(
            request=request,
            worker_node= worker_node,
            execution_time=time.time() - start_time,
            error_message=str(e)
        )
        return f"Error: Request {request_id}. Nodo: {worker_node}\n Error: {str(e)}"
    

    execution_time = time.time() - start_time

    AuditLog.objects.create(
        request=request,
        worker_node=worker_node,
        execution_time=execution_time
    )

    return f"OCR completado por {worker_node} en {execution_time:.2f}s"