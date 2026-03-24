/** @type {import('tailwindcss').Config} */
module.exports = {
  important: '#gb-dashboard',
  content: [
    './src/views/ProjectDashboardDemo.vue',
    './src/components/project-dashboard/**/*.{vue,js,ts}'
  ],
  theme: {
    extend: {
      colors: {
        gb: {
          text: 'var(--vl-text, #0d1733)',
          muted: 'var(--vl-muted, #5d6b8a)',
          border: 'var(--vl-border, #d8e0f0)',
          surface: 'var(--vl-surface, #ffffff)',
          soft: 'var(--vl-surface-soft, #f6f9ff)',
          primary: 'var(--vl-primary-end, #2754c7)',
          danger: 'var(--vl-danger, #d43b50)'
        }
      },
      fontFamily: {
        sans: ['Inter', 'SF Pro Text', 'system-ui', 'sans-serif']
      }
    }
  },
  plugins: []
};
