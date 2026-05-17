// @ts-check
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { defineConfig, fontProviders } from 'astro/config';

// https://astro.build/config
export default defineConfig({
	site: 'https://migukstory.com',
	integrations: [
		mdx(),
		sitemap({
			i18n: { defaultLocale: 'ko', locales: { ko: 'ko-KR' } },
		}),
	],
	markdown: {
		shikiConfig: { theme: 'github-light', wrap: true },
	},
	fonts: [
		{
			provider: fontProviders.google(),
			name: 'Gowun Batang',
			cssVariable: '--font-display',
			fallbacks: ['Georgia', 'serif'],
			weights: [400, 700],
			styles: ['normal'],
		},
	],
});
