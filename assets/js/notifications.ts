import { Notyf } from 'notyf';

export const toast = new Notyf({
    position: { x: 'center', y: 'bottom' },
    ripple: false,
    dismissible: true,
});
window.toast = toast;

declare global {
    interface Window {
        toast: Notyf,
    }
}
