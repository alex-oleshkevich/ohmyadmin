import { css, html, LitElement } from 'lit';
import { customElement, queryAssignedElements } from 'lit/decorators.js';

type BeforeSwapEvent = CustomEvent<{
    elt: HTMLElement,
    xhr: XMLHttpRequest,
    target: HTMLElement,
    requestConfig: any,
}>

declare global {
    interface HTMLElementEventMap {
        'htmx:beforeSwap': BeforeSwapEvent;
    }

    interface HTMLElementTagNameMap {
        'o-modals': ModalsElement,
    }
}


@customElement('o-modals')
export class ModalsElement extends LitElement {
    @queryAssignedElements({ selector: 'dialog' })
    dialogs!: HTMLDialogElement[];
    static override styles = css`:host {
        display: block
    }`;

    override render() {
        return html`
            <slot></slot>`;
    }

    protected override firstUpdated() {
        window.addEventListener('modals-close', this.closeActiveModal.bind(this));
        document.body.addEventListener('htmx:afterSettle', e => {
            if (!(e instanceof CustomEvent)) {
                return;
            }

            const target = e.target! as HTMLElement;
            const dialog: HTMLDialogElement | null = target.querySelector<HTMLDialogElement>('dialog[data-autoopen]');
            if (dialog) {
                dialog.addEventListener('close', () => dialog.remove());
                dialog.showModal();
            }
        });
    }

    closeActiveModal() {
        setTimeout(() => {
            this.dialogs.forEach(el => el.remove());
        }, 0);
    }
}

export const modals = {
    closeActive() {
        window.dispatchEvent(new CustomEvent('modals-close'));
    },
};
