import './components';
import { modals, toasts } from './components';
import { events } from './js/events';


const admin = {
    modals, toasts, events,
};

declare global {
    interface Window {
        ohmyadmin: typeof admin;
    }
}

window.ohmyadmin = admin;
