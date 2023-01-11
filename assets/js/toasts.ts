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
window.toast = toast;


// show flash messages as toasts
(window.__TOASTS__ || []).forEach(message => {
    toast.open({ type: message.category, message: message.message });
});
