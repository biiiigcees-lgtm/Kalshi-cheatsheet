import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './hooks/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Courier New"', 'monospace'],
      },
      colors: {
        bb: {
          bg:     '#000000',
          panel:  '#080808',
          border: '#1c1c1c',
          // Bloomberg amber — primary data colour
          amber:  '#ff8c00',
          // Up / positive
          green:  '#00d26a',
          // Down / negative
          red:    '#ff3b3b',
          // HOLD / caution
          yellow: '#ffd700',
          // Info / links
          blue:   '#4a9eff',
          // Dim labels
          dim:    '#4a4a4a',
          // Secondary text
          muted:  '#888888',
          // Primary labels
          text:   '#cccccc',
        },
      },
      keyframes: {
        blink: { '0%, 100%': { opacity: '1' }, '50%': { opacity: '0' } },
        'slide-in': { from: { transform: 'translateY(-4px)', opacity: '0' }, to: { transform: 'translateY(0)', opacity: '1' } },
      },
      animation: {
        blink:    'blink 1s step-end infinite',
        'slide-in': 'slide-in 0.15s ease-out',
      },
    },
  },
  plugins: [],
}

export default config
