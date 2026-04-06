"""
This module was created and tested with Python 3.11.
"""

import os
import time
import random
import re
from celery import shared_task
from .models import VerificationRequest, ExtractedData, AuditLog

def validate_ine_logic(extracted_data):
    """
    Calculate Logical Confidence based on INE data consistency.

    Checks for the presence and consistency of:
        - CURP
        - Clave de Elector
        - Date of Birth

    Returns a confidence score between 0 and 1.
    """
    
    score = 0.0
    
    curp = extracted_data.get('curp', '').upper()
    elector_key = extracted_data.get('clave_elector', '').upper()
    dob_short = extracted_data.get('dob_short', '')
    
    # CURP
    if re.match(r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[A-Z0-9][0-9]$', curp):
        score += 0.3
    else:
        print("curp does not match.")
    
    # Clave Elector
    if len(elector_key) == 18:
        score += 0.2
    else:
        print("clave_elector does not match.")
        
    # Birth Dates
    if dob_short and len(curp) >= 10 and len(elector_key) >= 12:
        curp_date = curp[4:10]        
        elector_date = elector_key[6:12] 
        
        if dob_short == curp_date == elector_date:
            score += 0.5  
        elif dob_short == curp_date or dob_short == elector_date:
            score += 0.25 
        else:
            print("birth_dates do not match.")
    else:
        print("dob_short (date of birth) coudn't be found by the OCR.")
            
    return round(score, 2)


def perform_face_match(id_image_path, face_image_path):
    """
    Compare the face in the ID image with the face in the selfie.

    Uses face_recognition (dlib-based) to calculate biometric similarity.
    Returns a tuple (is_same, confidence_score).
    """
    
    import math
    import face_recognition
    
    try:
        img_id = face_recognition.load_image_file(id_image_path)
        img_face = face_recognition.load_image_file(face_image_path)

        enc_id = face_recognition.face_encodings(img_id, num_jitters=10, model="large")
        enc_face = face_recognition.face_encodings(img_face, num_jitters=5, model="large")

        if not enc_id or not enc_face:
            return False, 0.0

        dist = face_recognition.face_distance([enc_id[0]], enc_face[0])[0]
        
        # Sigmoid function to convert distance to a confidence score between 0 and 1
        A = 20 
        B = 0.58
        
        score = 1 / (1 + math.exp(A * (dist - B)))
        
        # Threshold of 0.55 is commonly used for dlib-based face recognition to determine a match
        is_same = bool(dist <= 0.55)
        
        return is_same, round(score, 2)

    except Exception as e:
        print(f"ERROR DURING BIOMETRIC ANALYSIS (DLIB): {e}")
        return False, 0.0


def clean_alphanum_data(text, positions = [4, 5, 6, 7, 8, 9, 17]):
    """
    Apply OCR error corrections for alphanumeric data.

    Targets characters that are often misread in INE documents (e.g., 'O' vs '0').
    """
    
    mapping = {'O': '0', 'Z': '2', 'I': '1', 'A': '4', 'S': '5', 'B': '8'}
    
    chars = list(text.replace(" ", ""))

    for i in range(len(chars)):
        if i in positions and chars[i] in mapping:
            chars[i] = mapping[chars[i]]

    return "".join(chars)


def preprocess_image(image_path):
    """
    Preprocess image to enhance OCR accuracy.

    Includes grayscale conversion and Otsu's thresholding.
    """
    
    import cv2
    
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    return processed


def extract_ine_logic(ocr_results):
    """
    Extract structured data from OCR results based on INE document layout.
    """
    
    data = {}
    full_name = "No detectado"
    date_pattern = r'(\d{2})[\/\-\.](\d{2})[\/\-\.](\d{4})'
    
    for i, text in enumerate(ocr_results):

        clean_text = text.upper()

        if "NOMBRE" in clean_text or "NOYBRE" in clean_text and i + 3 < len(ocr_results):
            full_name = f"{ocr_results[i+2]} {ocr_results[i+3]}"
            if not ocr_results[i+4].startswith("DOMICIL"):
                full_name += f" {ocr_results[i+4]}"
        
        if "CURP" in clean_text and i + 2 < len(ocr_results):
            data['curp'] = clean_alphanum_data(ocr_results[i+2])
            
        if text.startswith("CLAVE") and i + 1 < len(ocr_results):
            clave_raw = text.split()[-1]
            data['clave_elector'] = clean_alphanum_data(clave_raw, positions=[6,7,8,9,10,11,12,13,15,16,17])

        date_match = re.search(date_pattern, clean_text)
        if date_match:
            day, month, year = date_match.groups()
            data['fecha_nacimiento'] = f"{day}/{month}/{year}"
            data['dob_short'] = f"{year[2:]}{month}{day}" # short version
            
    return full_name, data
    

@shared_task(bind=True)
def process_ocr_task(self, request_id):
    """
    Execute the identity verification workflow.

    Workflow includes OCR extraction and optional facial recognition.
    Calculates a Global Trust Score based on:
    - Face Confidence (70%)
    - Logical Confidence (25%)
    - Detection Confidence (5%)
    """
    
    import easyocr  
    
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
            full_name, structured_data = "Documento no soportado", {}

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
        w1, w2, w3 = 0.7, 0.25, 0.05
        final_score = (w1 * c_f) + (w2 * c_l) + (w3 * c_d)

        if request.is_verification_mode:
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
        return f"Error: Request {request_id}. Node: {worker_node}\n Error: {str(e)}"
    

    execution_time = time.time() - start_time

    AuditLog.objects.create(
        request=request,
        worker_node=worker_node,
        execution_time=execution_time
    )

    return f"OCR completed by {worker_node} in {execution_time:.2f}s"
