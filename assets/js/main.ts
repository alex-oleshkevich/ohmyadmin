import Alpine from 'alpinejs';
import './event_handlers';
import './globals.d';
import './components';
import { Events } from './events';

window.Alpine = Alpine;


Alpine.start();


function closeModal() {
    document.body.dispatchEvent(new CustomEvent(Events.ModalClose, { bubbles: true }));
}

window.closeModal = closeModal;
