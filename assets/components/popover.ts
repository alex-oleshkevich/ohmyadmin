import { html, LitElement } from 'lit';
import { customElement, property, queryAssignedElements } from 'lit/decorators.js';
import { styleMap } from 'lit/directives/style-map.js';
import { computePosition, autoUpdate, offset } from '@floating-ui/dom';
import { Placement } from '@floating-ui/utils';

@customElement('o-popover')
export class PopoverElement extends LitElement {
    @property({ reflect: true, type: Boolean })
    open = false;

    @property()
    trigger: string = '';

    @queryAssignedElements({ selector: '*:first-child' })
    floatingEl!: HTMLElement[];

    @property()
    placement: Placement = 'bottom';

    @property({ type: Number })
    offset = 12;

    protected override firstUpdated() {
        const triggered = () => this.open ? this.destroy() : this.setup();
        document.querySelector(this.trigger)?.addEventListener('click', triggered);
        document.addEventListener('click', e => {
            if (!this.open) {
                return;
            }

            if (document.querySelector(this.trigger)?.contains(e.target as HTMLElement)) {
                return;
            }

            if (!this.contains(e.target as HTMLElement)) {
                this.open = false;
            }
        });
    }

    private setup() {
        this.open = true;
        const triggerEl = document.querySelector(this.trigger);
        if (!triggerEl) {
            throw new Error('Trigger element not found.');
        }

        if (this.floatingEl.length == 0) {
            throw new Error('Empty slot.');
        }

        autoUpdate(triggerEl, this.floatingEl[0], () => {
            computePosition(triggerEl, this.floatingEl[0], {
                placement: this.placement,
                middleware: [offset(this.offset)],
            })
                .then(({ x, y }) => {
                    Object.assign(this.floatingEl[0].style, {
                        left: `${ x }px`,
                        top: `${ y }px`,
                    });
                });
        });
    }

    private destroy() {
        this.open = false;
    }

    override render(): unknown {
        const styles = styleMap({
            display: this.open ? 'block' : 'none',
        });
        return html`
            <slot style="${ styles }"></slot>`;
    }
}
