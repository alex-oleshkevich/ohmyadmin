const defaultColors = require('tailwindcss/colors');

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
        {pattern: /grid-cols/},
        {pattern: /max-w/},
        {pattern: /transform/},
        {pattern: /rotate-/},
    ],
    theme: {
        extend: {
            colors: {
                accent: defaultColors.blue
            }
        }
    },
    plugins: [
        require('@tailwindcss/forms'),
        require('tailwindcss/nesting'),
        require('@tailwindcss/typography'),
    ],
};
