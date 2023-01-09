module.exports = {
    content: [
        '../ohmyadmin/**/*.html',
        '../assets/**/*.ts',
        '../examples/**/*.html',
    ],
    plugins: [
        require('@tailwindcss/forms'),
        require('tailwindcss/nesting'),
        require('@tailwindcss/typography'),
    ],
};
