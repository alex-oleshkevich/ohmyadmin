import Alpine from 'alpinejs';
import './tables';
import './global_events';

window.Alpine = Alpine;

Alpine.start();

declare global {
    interface Window {
        Alpine: Alpine,
    }
}
