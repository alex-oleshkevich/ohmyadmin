import Alpine from 'alpinejs';

document.addEventListener('alpine:init', () => {
    Alpine.data('table', () => ({
        selected: [],
        batchAction: '',
        openBatchModal: false,
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
        runBatchAction() {
            this.openBatchModal = true;
        }
    }));
});