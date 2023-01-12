import { html, LitElement, PropertyValues } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { state } from 'lit/decorators/state.js';

@customElement('x-batch-toggle')
export class BatchToggleElement extends LitElement {
    @property({ type: Boolean }) checked: boolean = false;
    @property({ attribute: 'object-id' }) objectId: string = '';

    onInput(e: InputEvent) {
        this.dispatchEvent(new CustomEvent('rows.selected', { detail: this.objectId, bubbles: true }));
    }

    protected render(): unknown {
        return html`<input name="_ids" type="checkbox" @input="${ this.onInput }" value="${ this.objectId }"
                           ?checked="${ this.checked }"/>`;
    }

    protected createRenderRoot(): Element | ShadowRoot {
        return this;
    }
}

@customElement('x-batch-select-all')
export class BatchSelectAllElement extends LitElement {
    @property({ type: Boolean }) checked: boolean = false;

    onClick(e: InputEvent) {
        const ids: string[] = [];
        this.closest('#data')!
            .querySelectorAll('input[name="_ids"]')
            .forEach(el => {
                (el as HTMLInputElement).checked = (e.target as HTMLInputElement).checked;
                ids.push(el.value);
            });
        this.dispatchEvent(new CustomEvent('rows.select-all', { detail: ids, bubbles: true }));
    }

    protected render(): unknown {
        return html`<input type="checkbox" @change="${ this.onClick }" ?checked="${ this.checked }"/>`;
    }

    protected createRenderRoot(): Element | ShadowRoot {
        return this;
    }
}

@customElement('x-batch-selected-rows')
export class BatchSelectedRowsElement extends LitElement {
    @property({ type: Boolean }) checked: boolean = false;
    @state() selected: string[] = [];

    protected firstUpdated(_changedProperties: PropertyValues) {
        window.addEventListener('rows.selected', this.onRowSelected.bind(this));
        window.addEventListener('rows.select-all', this.onAllRowsSelected.bind(this));
        window.addEventListener('refresh-datatable', this.onDataRefresh.bind(this));
    }

    onDataRefresh() {
        this.selected = [];
        this.requestUpdate();
    }

    onRowSelected(e: Event | CustomEvent<string>) {
        if (e instanceof CustomEvent) {
            this._selectValue(e.detail);
            this.requestUpdate();
        }
    }

    onAllRowsSelected(e: Event | CustomEvent<string[]>) {
        if (e instanceof CustomEvent) {
            e.detail.forEach(this._selectValue.bind(this));
            this.requestUpdate();
        }
    }

    private _selectValue(value: string) {
        if (this.selected.includes(value)) {
            this.selected.splice(this.selected.indexOf(value), 1);
        } else {
            this.selected.push(value);
        }
    }

    protected render(): unknown {
        const rows = this.selected.map(id => html`
            <option value="${ id }" selected>${ id }</option>
        `);
        return html`<select name="_ids" multiple style="display: none">${ rows }</select>`;
    }

    protected createRenderRoot(): Element | ShadowRoot {
        return this;
    }
}
