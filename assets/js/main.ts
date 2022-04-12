import Alpine from 'alpinejs';
import {bindSubforms} from './forms';

window.Alpine = Alpine;

Alpine.start();

function onDocumentLoaded() {
    bindSubforms();
}

document.addEventListener('DOMContentLoaded', onDocumentLoaded);
