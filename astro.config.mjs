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
			name: 'Noto Sans KR',
			cssVariable: '--font-noto-kr',
			fallbacks: ['system-ui', 'sans-serif'],
			weights: [400, 500, 700],
			styles: ['normal'],
		},
		{
			provider: fontProviders.google(),
			name: 'Noto Serif KR',
			cssVariable: '--font-noto-serif-kr',
			fallbacks: ['serif'],
			weights: [400, 700],
			styles: ['normal'],
		},
	],
});
