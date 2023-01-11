import Alpine from 'alpinejs';
import { Notyf } from 'notyf';
import { ToastType } from './toasts';

declare global {
    interface Window {
        Alpine: Alpine,
        toast: Notyf,
        __TOASTS__: { category: ToastType, message: string }[],
        closeModal: () => void,
    }
}
export {};
