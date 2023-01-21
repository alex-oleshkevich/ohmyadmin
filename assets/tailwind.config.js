module.exports = {
    content: [
        '../ohmyadmin/**/*.html',
        '../assets/**/*.ts',
        '../examples/**/*.html',
    ],
    safelist: [
        {pattern: /grid-/},
        {pattern: /flex-/},
        {pattern: /gap-/},
        {pattern: /col-span/},
        {pattern: /max-w/},
    ],
    plugins: [
        require('@tailwindcss/forms'),
        require('tailwindcss/nesting'),
        require('@tailwindcss/typography'),
    ],
};
