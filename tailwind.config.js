/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html',
    './static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#C97B8A',
          light:   '#E8A4B2',
          dark:    '#A05565',
        },
        neutral: {
          dark:  '#333333',
          mid:   '#666666',
          light: '#F5F5F5',
        },
        success: '#5C9E6E',
        error:   '#C0392B',
        warning: '#D4A017',
      },
      fontFamily: {
        sans:    ['DM Sans', 'sans-serif'],
        serif:   ['Cormorant Garamond', 'serif'],
        display: ['Cormorant Garamond', 'serif'],
        script:  ['Dancing Script', 'cursive'],
      },
    },
  },
  plugins: [],
}
