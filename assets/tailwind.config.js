module.exports = {
    mode: 'jit',
    content: ['../ohmyadmin/**/*.html'],
    safelist: [
        {pattern: /text-blue/},
        {pattern: /text-red/},
        {pattern: /bg-blue/},
        {pattern: /bg-red/},
        {pattern: /transition/},
        {pattern: /opacity/},
        {pattern: /ease/},
        {pattern: /duration/},
    ],
    plugins: [
        require('@tailwindcss/forms'),
    ]
};
