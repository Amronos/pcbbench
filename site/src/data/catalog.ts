import { BACKPLANE_CLI, type Harness, type ModelId } from '@pcbbench/bench/runs';

type HarnessInfo = { name: string; url: string; about: (model: ModelId) => string };

export const HARNESSES: Record<Harness, HarnessInfo> = {
	'codex-desktop': {
		name: 'Codex desktop',
		url: 'https://openai.com/codex/',
		about: () => 'Codex in the ChatGPT desktop app, with computer use'
	},
	'codex-desktop-texttocad': {
		name: 'Codex desktop + text-to-cad',
		url: 'https://texttocad.dev/',
		about: () => 'Codex in the ChatGPT desktop app, with computer use and the text-to-cad plugin'
	},
	backplane: {
		name: 'Backplane',
		url: 'https://backplaneworks.com/',
		about: (model) =>
			`Backplane hub driving ${BACKPLANE_CLI[model] === 'claude' ? 'Claude Code' : 'Codex CLI'}`
	},
	sprocket: {
		name: 'Sprocket',
		url: 'https://usesprocket.dev/',
		about: () => 'Sprocket CLI with its KiCad connector'
	}
};

export const MODELS: Record<ModelId, { name: string; maker: string }> = {
	'opus-5.5': { name: 'Opus 5.5', maker: 'Anthropic' },
	'fable-5.2': { name: 'Fable 5.2', maker: 'Anthropic' },
	'gpt-6.1-sol': { name: 'GPT-6.1 Sol', maker: 'OpenAI' }
};

export const MACHINES = { mac: 'EC2 Mac (mac2-m2)', linux: 'EC2 Ubuntu (c7i.2xlarge)' } as const;
