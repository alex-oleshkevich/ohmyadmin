import Alpine from 'alpinejs';

import { Editor } from '@tiptap/core';
import { Level } from '@tiptap/extension-heading';
import { Image } from '@tiptap/extension-image';
import { Placeholder } from '@tiptap/extension-placeholder';
import { Link } from '@tiptap/extension-link';
import { Highlight } from '@tiptap/extension-highlight';

import StarterKit from '@tiptap/starter-kit';


export type RichEditorOptions = {
    editable?: boolean,
    placeholder?: string,
}

document.addEventListener('alpine:init', () => {
    Alpine.data('richEditor', (id: string, options?: RichEditorOptions) => {
        let editor: Editor;

        return {
            focused: false,
            ready: false,
            updateCounter: 0,
            init() {
                const self = this;
                const textarea = this.$refs.textarea;
                editor = new Editor({
                    element: this.$refs.editor,
                    editable: options?.editable ?? true,
                    content: textarea.value,
                    extensions: [
                        StarterKit.configure({
                            gapcursor: true,
                            document: true,
                        }),
                        Image.configure({
                            inline: true,
                        }),
                        Placeholder.configure({
                            emptyEditorClass: 're-empty',
                            placeholder: options?.placeholder || '',
                        }),
                        Link.configure({
                            protocols: ['mailto'],
                            openOnClick: false,
                        }),
                        Highlight.configure({}),
                    ],
                    onCreate({ editor }) {
                        self.updateCounter += 1;
                        self.ready = true;
                    },
                    onUpdate({ editor }) {
                        self.updateCounter += 1;
                        textarea.value = editor.getHTML();
                    },
                    onSelectionUpdate({ editor }) {
                        self.updateCounter += 1;
                    },
                    onFocus() {
                        self.focused = true;
                    },
                    onBlur() {
                        self.focused = false;
                    },
                });
            },
            isLoaded() {
                console.log('is loaded', editor);
                return editor;
            },
            isActive(action: string, _:any, opts?: any) {
                console.log(action, _, opts)
                return editor.isActive(action, opts);
            },
            toggle(action: string, opts?) {
                const actionMap: Record<string, any> = {
                    'bold': () => editor.chain().toggleBold().focus().run(),
                    'italic': () => editor.chain().toggleItalic().focus().run(),
                    'blockquote': () => editor.chain().toggleBlockquote().focus().run(),
                    'bullet_list': () => editor.chain().toggleBulletList().focus().run(),
                    'ordered_list': () => editor.chain().toggleOrderedList().focus().run(),
                    'code': () => editor.chain().toggleCode().focus().run(),
                    'code_block': () => editor.chain().toggleCodeBlock().focus().run(),
                    'heading': (level: Level) => editor.chain().toggleHeading({ level }).focus().run(),
                    'link': ({ href, target }) => editor.commands.toggleLink({ href, target }),
                    'highlight': () => editor.commands.toggleHighlight({ color: 'red' }),
                };
                actionMap[action](opts);
            },
            toggleHeading(level: Level) {
                editor.chain().toggleHeading({ level }).focus().run();
            }
        };
    });
});
