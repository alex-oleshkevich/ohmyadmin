import { toast, ToastType } from './notifications';

export const Events = {
    Toast: 'toast',
    DismissModal: 'modals.dismiss',
} as const;

type ToastOptions = {
    message: string,
    category: ToastType,
}

function onToastEvent(e: Event | CustomEvent<ToastOptions>) {
    if (e instanceof CustomEvent) {
        toast.open({ type: e.detail.category, message: e.detail.message });
    }
}

document.body.addEventListener(Events.Toast, onToastEvent);

type HtmxErrorResponseType = {
    elt: HTMLElement,
    error: string,
    etc: Record<any, any>,
    failed: boolean,
    pathInfo: {
        anchor: string | undefined,
        finalRequestPath: string,
        requestPath: string,
        responsePath: string,
        successful: boolean,
        target: HTMLElement,
        xhr: XMLHttpRequest,
    }
}

function onHTMXResponseError(e: CustomEvent<HtmxErrorResponseType> | Event) {
    if (e instanceof CustomEvent) {
        toast.error(e.detail.error);
    }
}

document.body.addEventListener('htmx:responseError', onHTMXResponseError);
