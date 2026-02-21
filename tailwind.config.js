/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        'bg-primary': '#0D0D0F',
        'bg-secondary': '#1A1A2E',
        'bg-tertiary': '#2A2A3E',
        'pink-500': '#EC4899',
        'magenta-500': '#D946EF',
        'rose-400': '#FB7185',
      },
      fontFamily: {
        sans: ['system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
};
