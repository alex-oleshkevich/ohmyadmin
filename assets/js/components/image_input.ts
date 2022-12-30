import { customElement, property } from 'lit/decorators.js';
import { ref, Ref, createRef } from 'lit/directives/ref.js';
import { classMap } from 'lit/directives/class-map.js';
import { html, LitElement, svg } from 'lit';


const placeholder = svg`
<div class="bg-gray-100">
    <svg class="h-full w-full text-gray-300" fill="currentColor" viewBox="0 0 24 24">
      <path d="M24 20.993V24H0v-2.996A14.977 14.977 0 0112.004 15c4.904 0 9.26 2.354 11.996 5.993zM16.002 8.999a4 4 0 11-8 0 4 4 0 018 0z"></path>
    </svg>
</div>`;

export type ImageInputSize = 'small' | 'large';
export type ImageInputShape = 'circle' | 'square';

@customElement('x-image-field')
export class ImageInput extends LitElement {
    @property() id: string = '';
    @property() name: string = '';
    @property({ type: Array, converter: value => value?.split(',') }) accept: string[] = [];
    @property({ attribute: 'preview-image', reflect: true }) previewImage: string = '';
    @property({ attribute: 'delete-label' }) deleteLabel: string = 'Delete';
    @property({ attribute: 'button-label' }) buttonLabel: string = 'Change';
    @property() size: ImageInputSize = 'small';
    @property() shape: ImageInputShape = 'circle';


    private inputRef: Ref<HTMLInputElement> = createRef();

    onButtonClicked() {
        this.inputRef.value?.click();
    }

    onFileSelected(e: InputEvent) {
        const target = e.target as HTMLInputElement;
        if (!target.files) return;
        const file = target.files[0];
        this.previewImage = URL.createObjectURL(file);
        this.requestUpdate();
    }

    protected render(): unknown {
        const image = this.previewImage ? html`<img class="h-full w-full"
                                                    src="${ this.previewImage }">` : placeholder;
        const accept = this.accept.join(',');

        let height = 20;
        let width = 20;
        if (this.size == 'large') {
            height = 40;
            width = 40;

            if (this.shape == 'square') {
                width = 64;
            }
        }


        const classes = classMap({
            'rounded-full': this.shape == 'circle',
            'rounded-md': this.shape == 'square',
            [`h-${ height }`]: true,
            [`w-${ width }`]: true,
        });

        return html`
            <div class="flex items-center gap-5">
                <div class="overflow-hidden ${ classes }">${ image }</div>
                <div class="flex flex-col gap-3 justify-center">
                    <button type="button" class="btn" @click="${ this.onButtonClicked }">${ this.buttonLabel }</button>
                    <label class="text-sm">
                        <input type="checkbox" name="${ this.name }-delete"> ${ this.deleteLabel }
                    </label>
                </div>
                <input style="display: none"
                       type="file"
                       id="${ this.id }"
                       name="${ this.name }"
                       accept="${ accept }"
                       @input="${ this.onFileSelected }"
                       ${ ref(this.inputRef) }>
            </div>`;
    }

    protected createRenderRoot(): Element | ShadowRoot {
        return this;
    }
}
