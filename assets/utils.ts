export const resolveColor = (value: string) => {
    if (value.startsWith('var(')) {
        const variable = value.match(/\((.*)\)/)![1];
        return getComputedStyle(document.documentElement).getPropertyValue(variable);
    }
    if (value.startsWith('--')) {
        return getComputedStyle(document.documentElement).getPropertyValue(value);
    }
    return value;
};
