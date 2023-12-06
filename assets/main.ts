import './components';
import { modals, toasts } from './components';


const admin = {
    modals, toasts,
};

declare global {
    interface Window {
        ohmyadmin: typeof admin;
    }
}

window.ohmyadmin = admin;
