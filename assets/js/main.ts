import Alpine from 'alpinejs';
import './tables';
import './actions';
import './global_events';
import './globals.d';
import { Events } from './global_events';

window.Alpine = Alpine;

document.addEventListener('alpine:init', () => {
    Alpine.data('app', () => ({
        actionUrl: '',
        init() {
            document.body.addEventListener(Events.DismissModal, () => {
                this.closeActionModal();
            });
        },
        get isActionModalOpen() {
            return this.actionUrl != '';
        },
        openActionModal(actionUrl: string) {
            this.actionUrl = actionUrl;
        },
        closeActionModal() {
            this.actionUrl = '';
        }
    }));
});

Alpine.start();
