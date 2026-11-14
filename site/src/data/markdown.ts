import { Marked } from 'marked';

// Maps a relative path in the document to a URL, or to null to drop the link and keep its text.
type Resolve = (path: string) => string | null;

const isRelative = (href: string) => !/^([a-z]+:|#|\/)/i.test(href);

const escapeHtml = (text: string) =>
	text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');

export function renderMarkdown(source: string, resolve: { link: Resolve; image: Resolve }) {
	const marked = new Marked({
		gfm: true,
		async: false,
		renderer: {
			// Agent and judge documents are shown as text, never as live HTML.
			html: ({ text }) => escapeHtml(text),
			link({ href, tokens }) {
				const text = this.parser.parseInline(tokens);
				const target = isRelative(href) ? resolve.link(href.replace(/^\.\//, '')) : href;

				return target ? `<a href="${target}">${text}</a>` : text;
			},
			image({ href, text }) {
				const target = isRelative(href) ? resolve.image(href.replace(/^\.\//, '')) : href;

				return target ? `<img src="${target}" alt="${escapeHtml(text)}" loading="lazy">` : '';
			}
		}
	});

	return marked.parse(source, { async: false });
}
