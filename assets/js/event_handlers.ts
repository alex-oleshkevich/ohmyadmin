import { toast, ToastOptions } from './toasts';
import { Events } from './events';
import { ModalElement } from './components';


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


function popModal() {
    const topMostModal: ModalElement | null = document.querySelector('#modals [data-modal-wrapper]:first-child');
    if (!topMostModal) return;
    topMostModal.close();
}

document.addEventListener(Events.ModalClose, popModal);
