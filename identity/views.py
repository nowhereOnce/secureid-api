from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import IdentityUploadForm
from .tasks import process_ocr_task
from .models import VerificationRequest

def privacy_view(request):
    return render(request, 'identity/privacy.html')

@login_required
def upload_identity(request):
    if request.method == 'POST':
        form = IdentityUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # obj: VerificationRequest instance
            obj = form.save(commit=False)
            obj.user = request.user

            obj.is_verification_mode = "mode_toggle" in request.POST
            if obj.is_verification_mode and 'face_image' in request.FILES:
                obj.face_image = request.FILES['face_image']

            obj.save()
            
            # Start the OCR processing task asynchronously
            process_ocr_task.delay(str(obj.id))
            
            return redirect('verification_detail', pk=obj.id)
    else:
        form = IdentityUploadForm()
    return render(request, 'identity/upload.html', {'form': form})

@login_required
def verification_detail(request, pk):
    # Only allow access to the verification details if the request belongs to the user
    verification = get_object_or_404(VerificationRequest, pk=pk, user=request.user)
    return render(request, 'identity/detail.html', {'verification': verification})