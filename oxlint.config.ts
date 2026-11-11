const config = {
	ignorePatterns: ['runs/**', '.worktrees/**'],
	plugins: ['typescript', 'unicorn', 'oxc'],
	categories: { correctness: 'error' },
	rules: {
		'no-var': 'error',
		'prefer-const': 'error',
		'no-unused-vars': ['error', {}],
		'typescript/no-explicit-any': 'error',
		'typescript/consistent-type-assertions': ['error', { assertionStyle: 'never' }]
	}
};

export default config;
