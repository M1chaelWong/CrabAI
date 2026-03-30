from __future__ import annotations

import httpx
from app.tools.base import BaseTool


class WebSearchTool(BaseTool):
    """Search the web using DuckDuckGo Instant Answer API."""

    name = "web_search"
    description = "Search the web for current information. Use this when asked about recent events, news, or anything that requires up-to-date information."

    def get_definition(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    },
                },
                "required": ["query"],
            },
        }

    async def execute(self, tool_input: dict) -> str:
        query = tool_input.get("query", "")
        if not query:
            return "Error: empty search query"

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Use DuckDuckGo HTML search for better results
                resp = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={"User-Agent": "Mozilla/5.0 (compatible; CrabAI/1.0)"},
                    follow_redirects=True,
                )
                resp.raise_for_status()

                # Parse results from HTML
                results = self._parse_results(resp.text)
                if not results:
                    return f"No results found for: {query}"

                return f"Search results for '{query}':\n\n" + "\n\n".join(results[:5])

        except Exception as e:
            return f"Search error: {str(e)}"

    def _parse_results(self, html: str) -> list[str]:
        """Extract search results from DuckDuckGo HTML response."""
        results = []
        # Simple HTML parsing without BeautifulSoup
        parts = html.split('class="result__a"')
        for part in parts[1:8]:  # Skip first split, take up to 7
            # Extract title
            title_end = part.find("</a>")
            if title_end == -1:
                continue
            title_html = part[:title_end]
            # Remove HTML tags from title
            title = ""
            in_tag = False
            for ch in title_html:
                if ch == "<":
                    in_tag = True
                elif ch == ">":
                    in_tag = False
                elif not in_tag:
                    title += ch
            title = title.strip().lstrip(">").strip()

            # Extract snippet
            snippet = ""
            snippet_start = part.find('class="result__snippet"')
            if snippet_start != -1:
                snippet_content = part[snippet_start:]
                snippet_end = snippet_content.find("</a>")
                if snippet_end == -1:
                    snippet_end = snippet_content.find("</span>")
                if snippet_end != -1:
                    snippet_html = snippet_content[:snippet_end]
                    in_tag = False
                    for ch in snippet_html:
                        if ch == "<":
                            in_tag = True
                        elif ch == ">":
                            in_tag = False
                        elif not in_tag:
                            snippet += ch
                    snippet = snippet.strip().lstrip(">").strip()

            # Extract URL
            url = ""
            href_start = part.find('href="')
            if href_start != -1:
                href_content = part[href_start + 6:]
                href_end = href_content.find('"')
                if href_end != -1:
                    url = href_content[:href_end]

            if title:
                result = f"**{title}**"
                if url:
                    result += f"\n{url}"
                if snippet:
                    result += f"\n{snippet}"
                results.append(result)

        return results
