import { html, LitElement, PropertyValues } from 'lit';
import { customElement, queryAssignedElements } from 'lit/decorators.js';
import { state } from 'lit/decorators/state.js';
import { autoPlacement, autoUpdate, computePosition, offset } from '@floating-ui/dom';
import { OnClickOutsideController } from './click_outside';

declare global {
    // interface HTMLElementEventMap {
    //     'htmx:beforeSwap': BeforeSwapEvent;
    // }

    interface HTMLElementTagNameMap {
        'o-dropdown-menu': DropdownMenu,
        'o-dropdown-menu-trigger': DropdownMenuTrigger,
        'o-dropdown-menu-popup': DropdownMenuPopup,
    }
}


@customElement('o-dropdown-menu')
export class DropdownMenu extends LitElement {
    clickOutside = new OnClickOutsideController(this, () => {
        if (this.isOpen) {
            this.hide();
        }
    });

    @state()
    isOpen = false;

    @queryAssignedElements({ slot: 'trigger' })
    triggerNodes!: HTMLElement[];

    @queryAssignedElements({ slot: 'menu' })
    dropdownNodes!: HTMLElement[];

    onClickedOutside() {
        console.log('clicked outside');
    }

    onTrigger() {
        if (this.isOpen) {
            this.hide();
        } else {
            this.show();
        }
    }

    show() {
        this.isOpen = true;
        this.menu.style.display = 'block';
    }

    hide() {
        this.isOpen = false;
        this.menu.style.display = 'none';
    }

    get trigger(): HTMLElement {
        return this.triggerNodes[0];
    }

    get menu(): HTMLElement {
        return this.dropdownNodes[0];
    }

    protected override firstUpdated(_changedProperties: PropertyValues) {
        super.firstUpdated(_changedProperties);
        this.addEventListener('dropdown-trigger', this.onTrigger);

        this.bind();
    }

    bind() {
        autoUpdate(this.trigger, this.menu, () => {
            computePosition(this.trigger, this.menu, {
                placement: 'bottom-end',
                middleware: [
                    offset({
                        crossAxis: 0,
                        mainAxis: 12,
                        alignmentAxis: 0,
                    }),
                    autoPlacement({
                        allowedPlacements: ['bottom-end', 'bottom', 'bottom-start'],
                    }),
                ],
            })
                .then(({ x, y }) => {
                    Object.assign(this.menu.style, {
                        left: `${ x }px`,
                        top: `${ y }px`,
                    });
                });
        });
    }

    protected override render(): unknown {
        return html`
            <slot name="trigger"></slot>
            <slot name="menu"></slot>
        `;
    }
}


@customElement('o-dropdown-menu-trigger')
export class DropdownMenuTrigger extends LitElement {

    protected override firstUpdated() {
        if (this.children.length > 1) {
            throw new Error('<o-dropdown-menu-trigger> must have exactly one child element.');
        }

        this.children[0].addEventListener('click', this.trigger);
    }

    override disconnectedCallback() {
        this.children[0].removeEventListener('click', this.trigger);
        super.disconnectedCallback();
    }

    trigger() {
        this.dispatchEvent(new CustomEvent('dropdown-trigger', { bubbles: true }));
    }

    protected override render(): unknown {
        return html`
            <slot></slot>`;
    }
}

@customElement('o-dropdown-menu-popup')
export class DropdownMenuPopup extends LitElement {
    protected override render(): unknown {
        if (this.children.length > 1) {
            throw new Error('<o-dropdown-menu-trigger> must have exactly one child element.');
        }
        return html`
            <slot></slot>
        `;
    }
}
