import Alpine from 'alpinejs';
import {Notyf} from 'notyf';
import {ToastType} from './notifications';

declare global {
    interface Window {
        Alpine: Alpine,
        toast: Notyf,
        __TOASTS__?: { category: ToastType, message: string }[],
        __ACTIONS__?: { [key: string]: string },
    }
}
export {};
