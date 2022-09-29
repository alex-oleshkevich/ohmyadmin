import Alpine from 'alpinejs';
import './tables';
import './actions';
import './global_events';
import './globals.d';
import {Events} from './global_events';

window.Alpine = Alpine;

document.addEventListener('alpine:init', () => {
    Alpine.data('app', () => ({
        actionUrl: '',
        init() {
            document.body.addEventListener(Events.DismissModal, () => {
                this.closeActionModal();
            });
        },

        /* modal handler */
        callBatchAction(actionId, objectIDs) {
            const action = window.__ACTIONS__[actionId];
            if (!action) {
                throw new Error(`Unregistered action ${actionId}.`);
            }
            const url = new URL(action);
            objectIDs.forEach(objectId => url.searchParams.append('object_id', objectId));
            this.actionUrl = url;
        },
        callAction(actionId) {
            const action = window.__ACTIONS__[actionId];
            if (!action) {
                throw new Error(`Unregistered action ${actionId}.`);
            }
            this.actionUrl = action;
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
