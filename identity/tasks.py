import easyocr
import cv2
import numpy as np
import os
import time
import random
from celery import shared_task
from .models import VerificationRequest, ExtractedData, AuditLog

def clean_curp(text):
    """Limpia confusiones comunes de OCR en el CURP."""
    mapping = {'O': '0', 'Z': '2', 'I': '1', 'A': '4', 'S': '5', 'B': '8'}
    # El CURP tiene números en las posiciones 4-9 y en la última
    chars = list(text.replace(" ", ""))
    for i in range(len(chars)):
        if i in [4, 5, 6, 7, 8, 9, 17] and chars[i] in mapping:
            chars[i] = mapping[chars[i]]
    return "".join(chars)

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

        # 1. Pre-procesamiento con OpenCV para mejorar contraste
        img = cv2.imread(request.image.path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Aplicamos un filtro para resaltar el texto negro sobre el fondo claro
        processed_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        # 2. Ejecutar EasyOCR
        reader = easyocr.Reader(['es'], gpu=True)
        # Pasamos la imagen procesada como array de numpy
        result = reader.readtext(processed_img, detail=0)

        # 3. Lógica de extracción por palabras clave
        full_name = "No detectado"
        curp = "No detectado"
        
        for i, text in enumerate(result):
            clean_text = text.upper()
            if "NOMBRE" in clean_text and i + 1 < len(result):
                # Usualmente el nombre son las siguientes 2 o 3 líneas
                full_name = f"{result[i+2]} {result[i+4]}"
            if "CURP" in clean_text and i + 1 < len(result):
                curp = clean_curp(result[i+2])

        # Save
        ExtractedData.objects.update_or_create(
            request=request,
            defaults={
                'full_name': full_name,
                'document_number': curp,
                'confidence_score': 0.98,
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