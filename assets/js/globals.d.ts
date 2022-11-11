import Alpine from 'alpinejs';
import { Notyf } from 'notyf';
import {createRichEditor} from './editor';
import { ToastType } from './notifications';

declare global {
    interface Window {
        Alpine: Alpine,
        toast: Notyf,
        __TOASTS__: { category: ToastType, message: string }[],
        __ACTIONS__: { [key: string]: string },
        __ACTION_ENDPOINT__?: string,
    }
}
export {};
