import Alpine from 'alpinejs';
import './tables';
import './actions';
import './global_events';
import './globals.d';
import { Events } from './global_events';

window.Alpine = Alpine;
type Choice = [string | number, string];
type ChoiceCache = Record<string, Choice[]>;
const loaderCache: ChoiceCache = {};

document.addEventListener('alpine:init', () => {
    Alpine.data('app', () => ({
        actionUrl: '',
        init() {
            document.body.addEventListener(Events.DismissModal, () => {
                this.closeActionModal();
            });
        },

        /* modal handler */
        callBatchAction(actionId: string, objectIDs: string[]) {
            this.callAction(actionId, { 'object_id': objectIDs });
        },
        callAction(actionId: string, args: Record<string, any>) {
            if (!window.__ACTION_ENDPOINT__) {
                throw new Error('__ACTION_ENDPOINT__ is undefined. Probably you call the action from invalid context.');
            }

            args = args || {};
            const url = new URL(window.__ACTION_ENDPOINT__);
            url.searchParams.set('_action', actionId);
            Object.entries<any>(args).forEach(([name, value]) => {
                if (Array.isArray(value)) {
                    value.forEach(val => url.searchParams.append(name, val));
                } else {
                    url.searchParams.set(name, value);
                }
            });
            this.actionUrl = url.toString();
        },
        closeActionModal() {
            this.actionUrl = '';
        },

        /* index page */
        selected: [] as string[],
        select(id: string) {
            if (this.selected.includes(id)) {
                this.selected.splice(this.selected.indexOf(id), 1);
            } else {
                this.selected.push(id);
            }
        },
        toggleSelectAll(e: any) {
            let checkboxes: HTMLInputElement[] = e.target.closest('table').querySelectorAll('tbody input[type="checkbox"]');
            if (e.target.checked) {
                checkboxes.forEach(el => {
                    this.selected.push(el.value);
                });
            } else {
                this.selected = [];
            }
        },
    }));

    Alpine.data('select', ({ value = '', loader = '' }) => ({
        value: '',
        loader: loader,
        state: 'idle' as 'idle' | 'loading',
        choices: [] as Choice[],
        init() {
            this.fetchChoices().then(() => {
                this.value = value;
            });
        },
        async fetchChoices() {
            if (loaderCache[loader]) {
                this.choices = loaderCache[loader];
            } else {
                this.state = 'loading';
                const url = new URL(window.__FIELD_AUTOCOMPLETE_ENDPOINT__);
                url.searchParams.set('loader', this.loader);
                const choices = await fetch(url).then(res => res.json().then(data => data));
                loaderCache[loader] = choices;
                this.choices = choices;
                this.state = 'idle';
            }
        }
    }));
});

Alpine.start();
