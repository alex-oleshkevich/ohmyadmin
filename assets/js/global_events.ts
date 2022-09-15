import { toast } from './notifications';

type ToastOptions = {
    message: string,
    category: 'error' | 'success',
}

document.body.addEventListener('toast', (e: CustomEvent<ToastOptions>) => {
    if (e.detail.category == 'success') {
        console.log(e.detail);
        toast.success(e.detail.message);
    } else {
        toast.error(e.detail.message);
    }
});
