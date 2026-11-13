import preact from '@astrojs/preact';
import { defineConfig, fontProviders } from 'astro/config';

// Vercel sets this to the production domain, which becomes the custom domain once one is added.
const productionHost = process.env.VERCEL_PROJECT_PRODUCTION_URL ?? 'localhost:4321';

export default defineConfig({
	site: `https://${productionHost}`,
	integrations: [preact()],
	fonts: [
		{
			provider: fontProviders.local(),
			name: 'Osifont',
			cssVariable: '--font-iso',
			fallbacks: ['sans-serif'],
			options: {
				variants: [{ src: ['./src/assets/fonts/osifont.woff2'], weight: 'normal', style: 'normal' }]
			}
		},
		{
			provider: fontProviders.fontsource(),
			name: 'Atkinson Hyperlegible Next',
			cssVariable: '--font-body',
			weights: ['200 800'],
			styles: ['normal', 'italic'],
			subsets: ['latin'],
			fallbacks: ['sans-serif']
		}
	]
});
