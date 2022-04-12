function removeRow(e: MouseEvent): void {
    e.target.closest('.subforms').removeChild(e.target.closest('.subform'));
}

function bindSubform(multiform: HTMLElement): void {
    let subforms: HTMLDivElement = multiform.querySelector('.subforms');
    let template: HTMLTemplateElement = multiform.querySelector('template');
    let addButton: HTMLButtonElement = multiform.querySelector('.add-row');

    subforms.querySelectorAll('.delete-row').forEach((delEl) => {
        delEl.addEventListener('click', removeRow);
    });

    addButton.addEventListener('click', () => {
        let rowCount = subforms.querySelectorAll('.subform').length;
        let docClone = template.content.cloneNode(true);

        docClone.querySelectorAll('input, textarea, select').forEach(input => {
            input.id = input.id.replace(/-([\d]+)-/, `-${ rowCount }-`);
            input.name = input.name.replace(/-([\d]+)-/, `-${ rowCount }-`);
            input.value = null;
        });
        docClone.querySelector('.delete-row').addEventListener('click', removeRow);
        subforms.appendChild(docClone);
    });
}

export function bindSubforms(): void {
    document.querySelectorAll('.multirow').forEach(bindSubform);
}
