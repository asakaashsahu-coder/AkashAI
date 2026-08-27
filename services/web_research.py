import html
import re
import urllib.parse
import urllib.request


class WebResearch:
    """
    Lightweight web research using DuckDuckGo's HTML search results.

    No paid search API or extra Python package is required.
    """

    def __init__(self):
        self.last_query = None
        self.last_results = []

    def _clean(self, value):
        value = re.sub(r"<[^>]+>", " ", value or "")
        value = html.unescape(value)
        return " ".join(value.split())

    def search(self, query, limit=6):
        query = str(query or "").strip()

        if not query:
            return []

        url = (
            "https://html.duckduckgo.com/html/?q="
            + urllib.parse.quote_plus(query)
        )

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/131 Safari/537.36"
                )
            }
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=10
            ) as response:
                page = response.read().decode(
                    "utf-8",
                    errors="replace"
                )
        except Exception as error:
            print("Web search error:", error)
            return []

        blocks = re.findall(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
            page,
            flags=re.I | re.S
        )

        snippets = re.findall(
            r'class="result__snippet"[^>]*>(.*?)</(?:a|div)>',
            page,
            flags=re.I | re.S
        )

        results = []

        for index, (href, title) in enumerate(blocks[:limit]):
            decoded = html.unescape(href)

            # DuckDuckGo wraps many external result URLs.
            parsed = urllib.parse.urlparse(decoded)
            params = urllib.parse.parse_qs(parsed.query)

            if "uddg" in params:
                decoded = params["uddg"][0]

            snippet = (
                self._clean(snippets[index])
                if index < len(snippets)
                else ""
            )

            results.append({
                "title": self._clean(title),
                "url": decoded,
                "snippet": snippet
            })

        self.last_query = query
        self.last_results = results
        return results

    def build_research_prompt(self, query, results):
        sources = []

        for index, result in enumerate(results, 1):
            sources.append(
                f"[{index}] {result['title']}\n"
                f"URL: {result['url']}\n"
                f"Search snippet: {result['snippet']}"
            )

        return (
            "Answer the user's question using the web search results below. "
            "Treat search snippets as potentially incomplete and do not invent "
            "facts that are not supported. Mention uncertainty when needed. "
            "At the end include a short 'Sources' section containing the "
            "numbered source titles and URLs you actually relied on.\n\n"
            f"USER QUESTION:\n{query}\n\n"
            "WEB SEARCH RESULTS:\n\n"
            + "\n\n".join(sources)
        )

    def format_results(self, results):
        if not results:
            return "I couldn't get web search results right now."

        lines = []

        for index, result in enumerate(results, 1):
            lines.append(
                f"{index}. {result['title']}\n"
                f"   {result['url']}"
            )

        return "🌐 Web results:\n\n" + "\n".join(lines)
