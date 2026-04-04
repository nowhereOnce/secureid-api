function copyToClipboard(elementId) {
    const copyText = document.getElementById(elementId);
    if (copyText) {
        copyText.select();
        copyText.setSelectionRange(0, 99999);
        navigator.clipboard.writeText(copyText.value);
        
        const btn = event.target;
        const originalText = btn.innerText;
        btn.innerText = "¡Copiado!";
        btn.style.background = "#27ae60";
        setTimeout(() => { 
            btn.innerText = originalText; 
            btn.style.background = "#34495e";
        }, 1500);
    }
}

// Auto reload if page is in processing state
const processingContainer = document.querySelector('.processing-container');
if (processingContainer) {
    setTimeout(function(){
        location.reload();
    }, 4000);
}
