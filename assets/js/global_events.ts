import { toast, ToastType } from './notifications';

export const Events = {
    Toast: 'toast',
    DismissModal: 'modals.dismiss',
} as const;

type ToastOptions = {
    message: string,
    category: ToastType,
}

document.body.addEventListener(Events.Toast, (e: CustomEvent<ToastOptions>) => {
    toast.open({ type: e.detail.category, message: e.detail.message });
});
