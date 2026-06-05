import js from '@eslint/js';
import ts from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';
import svelte from 'eslint-plugin-svelte';
import svelteParser from 'svelte-eslint-parser';
import prettier from 'eslint-config-prettier';
import globals from 'globals';

export default [
	js.configs.recommended,

	// TypeScript
	{
		files: ['**/*.ts'],
		languageOptions: {
			parser: tsParser,
			globals: { ...globals.browser }
		},
		plugins: { '@typescript-eslint': ts },
		rules: {
			...ts.configs.recommended.rules,
			'@typescript-eslint/no-explicit-any': 'warn',
			'@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }]
		}
	},

	// Svelte
	{
		files: ['**/*.svelte'],
		languageOptions: {
			parser: svelteParser,
			parserOptions: { parser: tsParser },
			globals: { ...globals.browser }
		},
		plugins: { svelte },
		rules: {
			...svelte.configs.recommended.rules,
			'svelte/no-unused-svelte-ignore': 'warn',
			'svelte/valid-compile': 'error'
		}
	},

	// Désactive les règles ESLint qui entrent en conflit avec Prettier
	prettier,

	{
		ignores: ['node_modules/**', '.svelte-kit/**', 'build/**', 'dist/**', 'src-tauri/**']
	}
];
