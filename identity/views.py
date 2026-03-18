from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import IdentityUploadForm
from .tasks import process_ocr_task
from .models import VerificationRequest

@login_required
def upload_identity(request):
    if request.method == 'POST':
        form = IdentityUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Guardamos la solicitud en Postgres (estado 'pending')
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            
            # DISPARAMOS LA TAREA ASÍNCRONA
            process_ocr_task.delay(str(obj.id))
            
            return redirect('verification_detail', pk=obj.id)
    else:
        form = IdentityUploadForm()
    return render(request, 'identity/upload.html', {'form': form})

@login_required
def verification_detail(request, pk):
    # Aseguramos que solo el dueño de la solicitud pueda verla
    verification = get_object_or_404(VerificationRequest, pk=pk, user=request.user)
    return render(request, 'identity/detail.html', {'verification': verification})