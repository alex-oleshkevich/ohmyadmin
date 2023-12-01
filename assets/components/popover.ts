import { html, LitElement } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('o-popover')
export class PopoverElement extends LitElement {
    @property({ reflect: true })
    open = false;

    @property()
    trigger: string = '';

    protected render(): unknown {
        if (this.open) {
            return html`
                <slot></slot>`;
        }

        return null;
    }
}
