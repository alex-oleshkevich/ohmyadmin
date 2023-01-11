import { LitElement } from 'lit';
import { customElement } from 'lit/decorators.js';

@customElement('x-modal')
export class ModalElement extends LitElement {
    close() {
        this.remove();
    }

    protected createRenderRoot(): Element | ShadowRoot {
        return this;
    }
}
