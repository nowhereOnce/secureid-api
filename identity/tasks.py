import easyocr
import cv2
import numpy as np
import os
import time
import random
from celery import shared_task
from .models import VerificationRequest, ExtractedData, AuditLog

def clean_alphanum_data(text, positions = [4, 5, 6, 7, 8, 9, 17]):
    """Limpia confusiones comunes de OCR en el CURP."""
    mapping = {'O': '0', 'Z': '2', 'I': '1', 'A': '4', 'S': '5', 'B': '8'}
    # El CURP tiene números en las posiciones 4-9 y en la última
    chars = list(text.replace(" ", ""))
    for i in range(len(chars)):
        if i in positions and chars[i] in mapping:
            chars[i] = mapping[chars[i]]
    return "".join(chars)

def preprocess_image(image_path):
    """Aplica filtros OpenCV para mejorar la precisión del OCR."""
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return processed

def extract_ine_logic(ocr_results):
    """Encapsula la lógica específica para la INE."""
    data = {}
    full_name = "No detectado"
    
    for i, text in enumerate(ocr_results):
        clean_text = text.upper()
        if "NOMBRE" in clean_text and i + 3 < len(ocr_results):
            full_name = f"{ocr_results[i+2]} {ocr_results[i+3]}"
            if not ocr_results[i+4].startswith("DOMICIL"):
                full_name += f" {ocr_results[i+4]}"
        
        if "CURP" in clean_text and i + 2 < len(ocr_results):
            data['curp'] = clean_alphanum_data(ocr_results[i+2])
            
        if text.startswith("CLAVE") and i + 1 < len(ocr_results):
            clave_raw = text.split()[-1]
            data['clave_elector'] = clean_alphanum_data(clave_raw, positions=range(18))
            
    return full_name, data

@shared_task(bind=True)
def process_ocr_task(self, request_id):
    """
    Simula el procesamiento pesado de OCR para una identificación.
    """
    start_time = time.time()
    worker_node = os.environ.get('WORKER_NAME', "Unknown-Node")
    
    try:
        request = VerificationRequest.objects.get(id=request_id)
        request.status = 'processing'
        request.save()

        # Preprocessing and reading 
        processed_img = preprocess_image(request.image.path)
        reader = easyocr.Reader(['es'], gpu=True)
        result = reader.readtext(processed_img, detail=0)

        # Extraction Logic 
        if request.document_type == "ine":
            full_name, structured_data = extract_ine_logic(result)
        else:
            full_name, structured_datta = "Documento no soportado", {}

        # Save
        ExtractedData.objects.update_or_create(
            request=request,
            defaults={
                'full_name': full_name,
                'structured_data': structured_data,
                'document_number': structured_data.get('curp', 'Not detected'),
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