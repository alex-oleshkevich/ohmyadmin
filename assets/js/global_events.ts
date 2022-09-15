import { toast, ToastType } from './notifications';

type ToastOptions = {
    message: string,
    category: ToastType,
}

document.body.addEventListener('toast', (e: CustomEvent<ToastOptions>) => {
    toast.open({ type: e.detail.category, message: e.detail.message });
});
