import { html, LitElement } from 'lit';
import { customElement, queryAssignedElements } from 'lit/decorators.js';


declare global {
    interface HTMLElementTagNameMap {
        'o-repeated-controller': RepeatedInputController,
        'o-repeated-input-item-controller': RepeatedInputItemController,
    }
}


@customElement('o-repeated-controller')
export class RepeatedInputController extends LitElement {

    @queryAssignedElements({ selector: '.repeated-input' })
    fieldSet!: HTMLDivElement[];

    counter: number = 0;

    get field(): HTMLDivElement {
        return this.fieldSet[0]!;
    }

    protected override firstUpdated() {
        this.counter = this.field.querySelectorAll('.repeated-input-set').length;
        this.querySelector('[data-repeated="add-item"]')?.addEventListener('click', this.onAddClicked.bind(this));
    }

    override disconnectedCallback() {
        super.disconnectedCallback();
        this.querySelector('[data-repeated="add-item"]')?.removeEventListener('click', this.onAddClicked.bind(this));
    }

    onAddClicked() {
        const template = this.field
            .querySelector<HTMLTemplateElement>('[data-repeated="template"]');
        if (!template) {
            throw Error('No repeated input template.');
        }

        const content = template.content.cloneNode(true) as HTMLElement;
        content
            .querySelectorAll<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>('input, select, textarea')
            .forEach((el) => {
                el.name = el.name.replace(':index', this.counter.toString());
                el.id = el.id.replace(':index', this.counter.toString());
            });
        this.counter += 1;

        const itemSet = this.field.querySelector<HTMLDivElement>('.repeated-input-set');
        itemSet?.append(content);
    }

    onRemoveClicked(e: Event) {
        (e.target as HTMLElement).closest('.repeated-input-item')?.remove();
    }

    protected override render(): unknown {
        return html`
            <slot></slot>`;
    }
}

@customElement('o-repeated-input-item-controller')
class RepeatedInputItemController extends LitElement {
    protected override firstUpdated() {
        const button = this.querySelector<HTMLButtonElement>('[data-repeated="remove-item"]');
        button!.addEventListener('click', this.remove.bind(this));
    }

    override disconnectedCallback() {
        super.disconnectedCallback();
        const button = this.querySelector<HTMLButtonElement>('[data-repeated="remove-item"]');
        button!.removeEventListener('click', this.remove.bind(this));
    }

    protected override render(): unknown {
        return html`
            <slot></slot>`;
    }
}
