module.exports = {
    content: [
        '../ohmyadmin/**/*.html',
        '../assets/**/*.ts',
        '../examples/**/*.html',
    ],
    safelist: [
        {pattern: /.*/},
    ],
    plugins: [
        require('@tailwindcss/forms'),
        require('@tailwindcss/aspect-ratio'),
    ]
};
