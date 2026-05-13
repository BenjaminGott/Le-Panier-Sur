/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				forest: {
					50: '#f3f8f3',
					100: '#e2eee3',
					200: '#c5dcc8',
					300: '#9bc3a1',
					400: '#6ea378',
					500: '#4d8559',
					600: '#3a6a45',
					700: '#305538',
					800: '#28442e',
					900: '#223827',
					950: '#101e14'
				},
				earth: {
					50: '#faf6f1',
					100: '#f3eadc',
					200: '#e6d3b8',
					300: '#d6b58c',
					400: '#c39564',
					500: '#b67d4a',
					600: '#a8693e',
					700: '#8b5235',
					800: '#714330',
					900: '#5d382a',
					950: '#321c14'
				},
				ocher: {
					50: '#fdf9ed',
					100: '#fbf0cc',
					200: '#f6df95',
					300: '#f1c757',
					400: '#edb12f',
					500: '#dc9319',
					600: '#bd7012',
					700: '#984f12',
					800: '#7d3f15',
					900: '#683516',
					950: '#3c1b07'
				},
				status: {
					excellent: '#2e7d32',
					bon: '#66a44e',
					mediocre: '#cda434',
					rejeter: '#e07c2a',
					toxique: '#c1333d',
					mortel: '#7a0e1a'
				}
			},
			fontFamily: {
				sans: [
					'"Inter"',
					'system-ui',
					'-apple-system',
					'"Segoe UI"',
					'Roboto',
					'sans-serif'
				],
				display: ['"Fraunces"', 'Georgia', 'serif']
			},
			boxShadow: {
				card: '0 2px 8px -2px rgba(34, 56, 39, 0.08), 0 8px 24px -8px rgba(34, 56, 39, 0.12)',
				'card-hover':
					'0 6px 16px -4px rgba(34, 56, 39, 0.18), 0 18px 36px -10px rgba(34, 56, 39, 0.22)'
			}
		}
	},
	plugins: []
};
