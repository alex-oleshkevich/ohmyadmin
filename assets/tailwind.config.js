module.exports = {
    mode: 'jit',
    content: ['../ohmyadmin/**/*.html'],
    safelist: [
        {pattern: /./},
    ],
    plugins: [
        require('@tailwindcss/forms'),
        require('@tailwindcss/aspect-ratio'),
    ]
};
