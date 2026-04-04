const imageInput = document.querySelector('input[type="file"]');
const preview = document.getElementById('image-preview');

if (imageInput) {
    imageInput.onchange = evt => {
        const [file] = imageInput.files;
        if (file) {
            preview.src = URL.createObjectURL(file);
            preview.style.display = 'block';
        }
    }
}

const toggle = document.getElementById('mode-toggle');
const selfieSection = document.getElementById('selfie-section');

if (toggle) {
    toggle.onchange = () => {
        selfieSection.style.display = toggle.checked ? 'block' : 'none';
    };
}
