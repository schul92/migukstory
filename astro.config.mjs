// @ts-check
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { defineConfig } from 'astro/config';

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
	// Note: Gowun Batang is loaded via direct Google Fonts CSS link in BaseHead
	// (with display=swap). Astro's font subsetter aggressively splits Korean
	// fonts into 180+ unicode-range subset files which bloats dist by 3MB.
	// Direct Google CSS uses their smarter dynamic subsetter (~5-10 files).
});
