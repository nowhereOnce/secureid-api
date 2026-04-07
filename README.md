# 🛡️ SecureID Engine

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/Django-5.0-092e20?style=for-the-badge&logo=django&logoColor=white" alt="Django Version">
  <img src="https://img.shields.io/badge/Celery-5.3-37814A?style=for-the-badge&logo=celery&logoColor=white" alt="Celery Version">
  <img src="https://img.shields.io/badge/Docker-24.0-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/AMD_ROCm-Hardware_Acc-ED1C24?style=flat-square&logo=amd&logoColor=white" alt="AMD GPU Support">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License">
  <a href="https://github.com/nowhereOnce"><img src="https://img.shields.io/badge/Developer-nowhereOnce-lightgrey?style=flat-square&logo=github" alt="Developer"></a>
</p>

<p align="center">
  <b>English</b> | <a href="README.es.md">Español</a>
</p>

---

### Distributed Identity Verification & Biometric Analysis System

**SecureID Engine** is an industrial-grade solution designed to automate identity validation, specifically optimized for Mexican identification documents (**INE**). The system leverages a containerized microservices architecture using **Docker**, utilizing asynchronous processing to ensure high availability, scalability, and performance.

<p align="center">
  <img src="screenshots/upload_page.png" width="600" alt="SecureID Dashboard">
</p>

-----

## 🚀 Core Features

The system offers two processing modalities configurable via the interface:

1.  **Extraction Mode (Lightweight OCR):**
    *   Automated extraction of critical metadata: **Full Name, CURP (Tax ID), Elector Key, and Date of Birth**.
    *   Ideal for fast onboarding flows where visual data consistency is the priority.

2.  **Verification Mode (Comprehensive Evaluation):**
    *   **Facial Biometrics:** Comparison of 128 facial landmarks between the ID photo and a live selfie using the `face_recognition` library (dlib-based).
    *   **Logical Consistency Engine (Triple-Check):** A proprietary algorithm that validates data integrity by cross-referencing the printed Date of Birth with the generation patterns of the CURP and Elector Key.
    *   **Global Trust Score:** Calculation of a global confidence index based on weighted parameters ($S = w_1 \cdot C_f + w_2 \cdot C_l + w_3 \cdot C_d$).

<p align="center">
  <img src="screenshots/verification_page.png" width="600" alt="SecureID Results">
</p>

-----

## 🛠️ Technology Stack

*   **Backend:** Django (Python 3.11).
*   **Asynchronous Processing:** Celery + Redis (Message Broker).
*   **Database:** PostgreSQL (Persistence for audit logs and results).
*   **Computer Vision & AI:**
    *   **EasyOCR:** Text extraction with GPU acceleration support.
    *   **OpenCV:** Image preprocessing (Otsu's Binarization) to enhance OCR precision.
    *   **Face Recognition (dlib):** Deep learning models for facial encoding.

-----

## 💻 System Requirements

To ensure optimal performance for Computer Vision models and asynchronous tasks, the following specifications are recommended:

| Component | CPU Version (Standard) | GPU Version (AMD ROCm) |
| :--- | :--- | :--- |
| **Processor** | 4+ Cores (Recommended) | 2+ Cores |
| **RAM** | 4GB (Min) / 8GB (Rec.) | 8GB (Min) |
| **GPU** | N/A | AMD RDNA2+ (e.g., RX 6600+) |
| **VRAM** | N/A | 4GB (Min) |
| **Storage** | ~5GB Free | 25GB+ Free (ROCm images are large) |
| **OS** | Linux / macOS / Windows | Linux (with KFD/amdgpu support) |

> **Note:** The GPU version requires specific AMD drivers and a ROCm-compatible kernel configuration.

-----

## 📦 Installation & Deployment

The project is fully containerized to ensure portability between development (CPU) and production (GPU) environments.

### 1. Environment Variables Configuration

Create a `.env` file in the root directory based on the following structure:

```env
# Database
POSTGRES_DB=secureid_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# Django
SECRET_KEY=django-insecure-your-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Celery / Redis
CELERY_BROKER_URL=redis://redis:6379/0
WORKER_NAME=Node-Alpha
```

### 2. Deployment with Docker

To run the system using **CPU only** (Lightweight version ~500MB for the Web container):

```bash
# Build and start containers
docker compose up -d --build

# Run database migrations
docker compose exec web python manage.py migrate

# Create superuser (Admin)
docker compose exec web python manage.py createsuperuser
```

-----

## 🖥️ System Usage

1.  **Web Portal (`/upload/`):** Upload the INE image and, if "Verification Mode" is active, a selfie. The system will dispatch the task to the Worker asynchronously.
2.  **Detail Dashboard (`/verification/<uuid>/`):** View results, confidence scores, and real-time task status.
3.  **Admin Portal (`/admin/`):** Manage all requests, review audit logs, and monitor execution times for each processing node.

<p align="center">
  <img src="screenshots/admin_page.png" width="600" alt="Admin Dashboard">
</p>

---

## ⚡ Hardware Acceleration (AMD ROCm / GPU)

For environments with compatible hardware (specifically AMD GPUs with RDNA2 architecture or higher), the system can offload OCR computation to the GPU to significantly reduce inference times.

### 1. Environment Setup (.env)
Define the following variables to enable the hardware engine:

```env
# Use the high-performance Dockerfile
WORKER_DOCKERFILE=Dockerfile.gpu

# Enable internal flag for GPU usage in EasyOCR and models
WORKER_GPU_ENABLED=true

# Specific compatibility for RX 6600/6650 XT (Navi 23)
HSA_OVERRIDE_GFX_VERSION=10.3.0
```

### 2. `docker-compose.yml` Modifications
To grant the container direct access to the video kernel and Linux render descriptors, update the `worker` section:

```yaml
  worker:
    build:
      context: .
      dockerfile: ${WORKER_DOCKERFILE:-Dockerfile}
    # ...
    # Direct access to acceleration hardware
    devices:
      - "/dev/kfd:/dev/kfd" # ROCm compute interface
      - "/dev/dri:/dev/dri" # Direct rendering
    
    # Required system groups for GPU access
    group_add:
      - video
      - render
    
    environment:
      - WORKER_GPU_ENABLED=${WORKER_GPU_ENABLED}
      - HSA_OVERRIDE_GFX_VERSION=${HSA_OVERRIDE_GFX_VERSION}
```

### 3. Technical Considerations
*   **Base Image:** GPU usage requires the `rocm/pytorch` image, which includes the necessary libraries for AMD driver communication on Linux (tested on CachyOS/Arch Linux). This version is significantly larger than the CPU-only version.

-----

## 🔒 Privacy & Data Handling (Demo & Open Source)

**SecureID Engine** is strictly a **demonstrative and open-source project**. As an on-premise, self-hosted solution, the entity or individual running the software instance is the sole data controller.

*   **Purpose:** Technical processing of official IDs (OCR & Biometrics) for identity validation.
*   **Processed Data:** Full name, CURP, Elector Key, and facial biometrics.
*   **Liability:** The original developer has no access, control, or visibility over any data, images, or results generated in external installations.

It is highly recommended to use this system in controlled test environments and delete sensitive data after completing technical validations.

-----

## 🙏 Special thanks

To **Ing. Angel Brito** for his invaluable feedback and technical insights. His suggestions were instrumental in elevating the quality of this project and ensuring professional standards from its initial release.

-----

## 👨‍💻 Author

**Enrique Alejandro Aguilar Ramos**
*Computer Engineer (UNAM)*
*Focus: Scalable Backend & AI Integration.*
[GitHub: nowhereOnce](https://github.com/nowhereOnce)
