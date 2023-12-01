import { Notyf } from 'notyf';

export type ToastType = 'success' | 'error';
export type ToastOptions = {
    message: string,
    category: ToastType,
}
export const toast = new Notyf({
    position: { x: 'center', y: 'bottom' },
    ripple: false,
    duration: 3000,
    dismissible: true,
});


function showPendingToasts() {
    const toasts: ToastOptions[] = window.__TOASTS__ || [];
    toasts.forEach(message => {
        toast.open({ type: message.category, message: message.message });
    });
}

document.addEventListener('DOMContentLoaded', showPendingToasts);

declare global {
    interface Window {
        toast: typeof Notyf;
        __TOASTS__: ToastOptions[];
    }
}
