import { Notyf } from 'notyf';

export type ToastType = 'success' | 'error';

export const toast = new Notyf({
    position: { x: 'center', y: 'bottom' },
    ripple: false,
    dismissible: true,
});
window.toast = toast;

declare global {
    interface Window {
        toast: Notyf,
        __TOASTS__?: { category: ToastType, message: string }[],
    }
}


// show flash messages as toasts
(window.__TOASTS__ || []).forEach(message => {
    toast.open({ type: message.category, message: message.message });
});
