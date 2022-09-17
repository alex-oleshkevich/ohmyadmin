import Alpine from 'alpinejs';

document.addEventListener('alpine:init', () => {
    Alpine.data('searchForm', (paramName: string, searchQuery: string) => ({
        searchQuery: searchQuery,
        onSubmit(event: SubmitEvent) {
            const form: HTMLFormElement = event.target as HTMLFormElement;
            const currentUrl = new URL(form.action);
            currentUrl.searchParams.set(paramName, this.searchQuery);
            location.href = currentUrl.toString();
        }
    }));
});
