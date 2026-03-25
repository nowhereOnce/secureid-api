import easyocr
import cv2
import numpy as np
import os
import time
import random
from celery import shared_task
from .models import VerificationRequest, ExtractedData, AuditLog
from deepface import DeepFace
import re
#from datetime import datetime


def validate_ine_logic(extracted_data):
    """
    Calcula Cl (Confianza Lógica). 
    Verifica estructura de CURP, Clave de Elector y su consistencia mutua.
    """
    score = 0.0
    validations = 0
    
    curp = extracted_data.get('curp', '').upper()
    elector_key = extracted_data.get('clave_elector', '').upper()
    
    # CURP
    if re.match(r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[A-Z0-9][0-9]$', curp):
        score += 0.4
    validations += 0.4
    
    # Clave Elector
    if len(elector_key) == 18:
        score += 0.3
    validations += 0.3
        
    # Birth Dates
    if curp and elector_key:
        curp_date = curp[4:10]
        elector_date = elector_key[6:12]
        if curp_date == elector_date:
            score += 0.3
        validations += 0.3
            
    return round(score, 2)


def perform_face_match(id_image_path, face_image_path):
    """
    Compara el rostro de la INE con la selfie subida.
    Retorna un score de confianza (0.0 a 1.0).
    """
    try:
        result = DeepFace.verify(
            img1_path = id_image_path, 
            img2_path = face_image_path,
            model_name = "Facenet512",
            enforce_detection = False, # evita que falle si la foto es borrosa
            detector_backend = "retinaface"
        )
        
        is_same = result['verified']
        score = 1.0 - result['distance'] # Normalizamos a score positivo
        return is_same, round(score, 2)

    except Exception as e:
        return False, 0.0


def clean_alphanum_data(text, positions = [4, 5, 6, 7, 8, 9, 17]):
    """Limpia confusiones comunes de OCR en el CURP."""
    mapping = {'O': '0', 'Z': '2', 'I': '1', 'A': '4', 'S': '5', 'B': '8'}
    
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
            data['clave_elector'] = clean_alphanum_data(clave_raw, positions=[6,7,8,9,10,11,12,13,15,16,17])
            
    return full_name, data
    

@shared_task(bind=True)
def process_ocr_task(self, request_id):
    """
    Executes the identity verification workflow through OCR and facial recognition.

    The Global Score is calculated using a weighted sum:
    Score = (0.5 * c_f) + (0.4 * c_l) + (0.1 * c_d)

    Where:
    - c_f (Face Confidence): Biometric similarity between the ID and the selfie.
    - c_l (Logical Confidence): Consistency of extracted data (INE validation logic).
    - c_d (Detection Confidence): Technical precision of the OCR engine (EasyOCR).

    This represents the final level of certainty regarding the authenticity and validity of the processed document.
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
        ocr_raw = reader.readtext(request.image.path, detail=1)

        if ocr_raw:
            c_d = sum([res[2] for res in ocr_raw]) / len(ocr_raw)
        else:
            c_d = 0.0
        
        result_text = [res[1] for res in ocr_raw]

        # Extraction Logic 
        if request.document_type == "ine":
            full_name, structured_data = extract_ine_logic(result_text)
        else:
            full_name, structured_datta = "Documento no soportado", {}

        c_l = validate_ine_logic(structured_data)

        # Face matching
        c_f = 0.0
        
        if request.is_verification_mode and request.face_image:
            is_same, face_score = perform_face_match(request.image.path, request.face_image.path)
            c_f = face_score
            structured_data['face_match'] = {
                'verified': is_same,
                'confidence_score': face_score
            }

        # GLOBAL VERIFICATION SCORE 
        w1, w2, w3 = 0.5, 0.4, 0.1
        final_score = (w1 * c_f) + (w2 * c_l) + (w3 * c_d)

        structured_data['metrics'] = {
            'face_confidence': round(c_f, 2),
            'logical_confidence': round(c_l, 2),
            'ocr_precision': round(c_d, 2),
            'global_score': round(final_score, 2)
        }

        # Save
        ExtractedData.objects.update_or_create(
            request=request,
            defaults={
                'full_name': full_name,
                'structured_data': structured_data,
                'document_number': structured_data.get('curp', 'Not detected'),
                'confidence_score': round(final_score, 2),
                'raw_json_response': {'detected_text': result_text}
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