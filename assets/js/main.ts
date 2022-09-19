import Alpine from 'alpinejs';
import './tables';
import './actions';
import './global_events';
import './globals.d';
import { Events } from './global_events';

window.Alpine = Alpine;

document.addEventListener('alpine:init', () => {
    Alpine.data('app', () => ({
        init() {
            document.body.addEventListener(Events.DismissModal, () => {
                this.closeActionModal();
            });
        },

        /* modal handler */
        actionUrl: '',
        get isActionModalOpen() {
            return this.actionUrl != '';
        },
        openActionModal(actionUrl: string, selected: string[] = null) {
            if (selected) {
                const url = new URL(actionUrl);
                selected.forEach(value => url.searchParams.append('selected', value));
                actionUrl = url.toString();
            }
            this.actionUrl = actionUrl;
        },
        selectObjectAndCallBatchAction(objectId: string, actionUrl: string) {
            this.selected = [objectId];
            this.actionUrl = actionUrl;
        },
        closeActionModal() {
            this.actionUrl = '';
        },

        /* index page */
        selected: [],
        select(id) {
            if (this.selected.includes(id)) {
                this.selected.splice(this.selected.indexOf(id), 1);
            } else {
                this.selected.push(id);
            }
        },
        toggleSelectAll(e) {
            let checkboxes = e.target.closest('table').querySelectorAll('tbody input[type="checkbox"]');
            if (e.target.checked) {
                checkboxes.forEach(el => {
                    this.selected.push(el.value);
                });
            } else {
                this.selected = [];
            }
        },
    }));
});

Alpine.start();
