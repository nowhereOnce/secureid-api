from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import IdentityUploadForm
from .tasks import process_ocr_task

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
            
            return render(request, 'identity/success.html', {'request_id': obj.id})
    else:
        form = IdentityUploadForm()
    return render(request, 'identity/upload.html', {'form': form})
