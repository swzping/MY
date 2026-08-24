// Common utility functions

function showToast(message, duration = 2000) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.remove('hidden');
    toast.offsetHeight; // Trigger reflow
    toast.classList.add('toast-show');

    setTimeout(() => {
        toast.classList.remove('toast-show');
        setTimeout(() => {
            toast.classList.add('hidden');
        }, 300);
    }, duration);
}

function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        return navigator.clipboard.writeText(text);
    }

    // Fallback
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    return Promise.resolve();
}

function saveToLocalStorage(key, value) {
    try {
        localStorage.setItem(key, value);
    } catch (e) {
        console.error('Failed to save to localStorage', e);
    }
}

function getFromLocalStorage(key, defaultValue = '') {
    try {
        const value = localStorage.getItem(key);
        return value === null ? defaultValue : value;
    } catch (e) {
        console.error('Failed to get from localStorage', e);
        return defaultValue;
    }
}