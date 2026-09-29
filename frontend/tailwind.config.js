/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // SOC-style dark palette.
        base: {
          950: '#070b14',
          900: '#0b1220',
          850: '#0f1a2e',
          800: '#131f38',
          700: '#1c2b4a',
          600: '#26385f',
        },
        accent: {
          DEFAULT: '#22d3ee',
          soft: '#0891b2',
        },
        risk: {
          low: '#22c55e',
          medium: '#eab308',
          high: '#f97316',
          critical: '#ef4444',
        },
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 20px rgba(34, 211, 238, 0.15)',
      },
    },
  },
  plugins: [],
};
