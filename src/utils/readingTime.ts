/**
 * Estimate Korean reading time.
 * Korean readers average ~500 characters per minute (vs ~250 words/min for English).
 */
export function estimateReadingTime(text: string): number {
	const cleaned = text
		.replace(/```[\s\S]*?```/g, '')   // strip code blocks
		.replace(/!\[.*?\]\(.*?\)/g, '')  // images
		.replace(/\[(.*?)\]\(.*?\)/g, '$1') // links keep text only
		.replace(/[#*_>\-]/g, '');
	const chars = cleaned.replace(/\s/g, '').length;
	const minutes = Math.max(1, Math.round(chars / 500));
	return minutes;
}
