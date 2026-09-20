import re
from dataclasses import dataclass, field

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None


@dataclass
class SearchResult:
    title: str = ""
    url: str = ""
    snippet: str = ""


@dataclass
class WebSearchResults:
    query: str = ""
    results: list = field(default_factory=list)
    raw_pages: list = field(default_factory=list)

    def to_context(self) -> str:
        lines = [f"Web search results for: {self.query}", ""]
        for i, r in enumerate(self.results, 1):
            lines.append(f"{i}. {r.title}")
            lines.append(f"   URL: {r.url}")
            lines.append(f"   {r.snippet}")
            lines.append("")
        if self.raw_pages:
            lines.append("=== Page Content ===")
            for page in self.raw_pages[:2]:
                lines.append(f"\n--- {page['url']} ---")
                lines.append(page.get("text", "")[:2000])
        return "\n".join(lines)


class WebSearch:
    MSFS_SEARCH_QUERIES = [
        "MSFS {error} fix",
        "Microsoft Flight Simulator {error} solution",
        "MSFS 2024 {error} crash fix",
        "flightsim.to {error} fix",
    ]

    def search(self, query: str, max_results: int = 5) -> WebSearchResults:
        if DDGS is None:
            return WebSearchResults(query=query)

        results = WebSearchResults(query=query)

        try:
            with DDGS() as ddgs:
                search_results = list(ddgs.text(query, max_results=max_results))
                for r in search_results:
                    results.results.append(SearchResult(
                        title=r.get("title", ""),
                        url=r.get("href", r.get("link", "")),
                        snippet=r.get("body", r.get("snippet", "")),
                    ))
        except Exception:
            pass

        return results

    def search_msfs_error(self, error_text: str, module: str = "", code: str = "") -> WebSearchResults:
        queries = []

        if module:
            queries.append(f"MSFS {module} crash fix")
            queries.append(f"{module} flight simulator error solution")

        if code:
            queries.append(f"MSFS error {code} fix")
            queries.append(f"exception {code} microsoft flight simulator")

        queries.append(f"MSFS {error_text[:80]} fix")

        for query in queries[:3]:
            results = self.search(query, max_results=3)
            if results.results:
                return results

        return self.search(f"Microsoft Flight Simulator crash {error_text[:60]}", max_results=5)

    def search_web(self, url: str) -> str:
        try:
            import requests
            resp = requests.get(url, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MSFS Diagnostics"
            })
            if resp.status_code == 200:
                text = resp.text
                text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                return text[:3000]
        except Exception:
            pass
        return ""
