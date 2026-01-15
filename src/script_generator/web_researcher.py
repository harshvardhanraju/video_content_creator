"""
Web Research Module for Script Generation

Searches the web for latest information, extracts facts,
and tracks sources for accurate, up-to-date content.
"""

import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time


@dataclass
class Source:
    """Represents a source article."""
    title: str
    url: str
    snippet: str
    published_date: Optional[str] = None
    domain: str = ""


@dataclass
class ResearchResult:
    """Contains all research findings."""
    topic: str
    category: str  # politics, economy, technology, etc.
    summary: str
    key_facts: List[str]
    timeline: List[Dict]  # chronological events
    sources: List[Source]
    related_topics: List[str]
    image_keywords: List[str]  # for image search
    research_timestamp: str = ""


class WebResearcher:
    """Research topics using web search and article extraction."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def research_topic(self, topic: str, max_sources: int = 8) -> ResearchResult:
        """
        Research a topic comprehensively.

        Args:
            topic: The topic to research
            max_sources: Maximum number of sources to fetch

        Returns:
            ResearchResult with facts, sources, and analysis
        """
        print(f"🔍 Researching: {topic}")

        # Step 1: Search for articles
        print("   Searching for latest articles...")
        search_results = self._search_web(topic, max_sources)

        # Step 2: Fetch and extract content from articles
        print(f"   Found {len(search_results)} sources, extracting content...")
        articles = self._fetch_articles(search_results)

        # Step 3: Categorize the topic
        category = self._categorize_topic(topic, articles)
        print(f"   Category: {category}")

        # Step 4: Extract key facts
        print("   Extracting key facts...")
        key_facts = self._extract_facts(articles, topic)

        # Step 5: Build timeline if applicable
        timeline = self._build_timeline(articles, topic)

        # Step 6: Generate summary
        summary = self._generate_summary(topic, key_facts, category)

        # Step 7: Extract image keywords
        image_keywords = self._extract_image_keywords(topic, key_facts, category)

        # Step 8: Find related topics
        related_topics = self._find_related_topics(articles, topic)

        # Convert search results to Source objects
        sources = [
            Source(
                title=r.get('title', ''),
                url=r.get('url', ''),
                snippet=r.get('snippet', ''),
                published_date=r.get('date'),
                domain=self._extract_domain(r.get('url', ''))
            )
            for r in search_results
        ]

        result = ResearchResult(
            topic=topic,
            category=category,
            summary=summary,
            key_facts=key_facts,
            timeline=timeline,
            sources=sources,
            related_topics=related_topics,
            image_keywords=image_keywords,
            research_timestamp=datetime.now().isoformat()
        )

        print(f"   ✅ Research complete: {len(key_facts)} facts, {len(sources)} sources")
        return result

    def _search_web(self, query: str, max_results: int) -> List[Dict]:
        """Search web using DuckDuckGo (no API key needed)."""
        results = []

        try:
            # Use DuckDuckGo HTML search
            search_url = "https://html.duckduckgo.com/html/"
            params = {'q': query}

            response = self.session.post(search_url, data=params, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract search results
            for result in soup.select('.result')[:max_results]:
                title_elem = result.select_one('.result__title')
                snippet_elem = result.select_one('.result__snippet')
                url_elem = result.select_one('.result__url')

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = ""

                    # Extract actual URL from DuckDuckGo redirect
                    link = title_elem.find('a')
                    if link and link.get('href'):
                        href = link.get('href')
                        # Parse DDG redirect URL
                        if 'uddg=' in href:
                            import urllib.parse
                            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                            url = parsed.get('uddg', [''])[0]
                        else:
                            url = href

                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    if title and url:
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet
                        })

        except Exception as e:
            print(f"   Warning: Web search failed: {e}")

        # Also try news-specific search
        try:
            news_results = self._search_news(query, max_results // 2)
            results.extend(news_results)
        except Exception:
            pass

        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for r in results:
            if r['url'] not in seen_urls:
                seen_urls.add(r['url'])
                unique_results.append(r)

        return unique_results[:max_results]

    def _search_news(self, query: str, max_results: int) -> List[Dict]:
        """Search for news articles specifically."""
        results = []

        try:
            # Search DuckDuckGo news
            news_url = "https://html.duckduckgo.com/html/"
            params = {'q': f"{query} site:reuters.com OR site:apnews.com OR site:bbc.com"}

            response = self.session.post(news_url, data=params, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')

            for result in soup.select('.result')[:max_results]:
                title_elem = result.select_one('.result__title')
                snippet_elem = result.select_one('.result__snippet')

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = title_elem.find('a')
                    url = ""
                    if link and link.get('href'):
                        href = link.get('href')
                        if 'uddg=' in href:
                            import urllib.parse
                            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                            url = parsed.get('uddg', [''])[0]

                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    if title and url:
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'is_news': True
                        })

        except Exception:
            pass

        return results

    def _fetch_articles(self, search_results: List[Dict]) -> List[Dict]:
        """Fetch and extract content from articles."""
        articles = []

        for result in search_results[:6]:  # Limit to avoid rate limiting
            try:
                url = result['url']
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Remove scripts, styles, nav
                    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                        tag.decompose()

                    # Extract article content
                    article_content = ""

                    # Try common article selectors
                    for selector in ['article', '.article-body', '.post-content',
                                     '.entry-content', 'main', '.content']:
                        content = soup.select_one(selector)
                        if content:
                            article_content = content.get_text(separator=' ', strip=True)
                            break

                    if not article_content:
                        # Fallback to body
                        article_content = soup.get_text(separator=' ', strip=True)

                    # Clean up content
                    article_content = re.sub(r'\s+', ' ', article_content)
                    article_content = article_content[:5000]  # Limit length

                    articles.append({
                        'title': result['title'],
                        'url': url,
                        'snippet': result['snippet'],
                        'content': article_content,
                        'domain': self._extract_domain(url)
                    })

                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                # Use snippet if fetch fails
                articles.append({
                    'title': result['title'],
                    'url': result['url'],
                    'snippet': result['snippet'],
                    'content': result['snippet'],
                    'domain': self._extract_domain(result['url'])
                })

        return articles

    def _categorize_topic(self, topic: str, articles: List[Dict]) -> str:
        """Categorize the topic based on content."""
        topic_lower = topic.lower()
        content = ' '.join([a.get('content', '') + ' ' + a.get('snippet', '') for a in articles]).lower()

        categories = {
            'politics': ['president', 'government', 'election', 'congress', 'senate',
                        'minister', 'diplomatic', 'policy', 'legislation', 'vote'],
            'economy': ['economy', 'market', 'stock', 'gdp', 'inflation', 'trade',
                       'tariff', 'financial', 'investment', 'dollar', 'currency'],
            'technology': ['ai', 'artificial intelligence', 'tech', 'software', 'app',
                          'startup', 'innovation', 'digital', 'data', 'algorithm'],
            'human_rights': ['human rights', 'refugee', 'asylum', 'immigration',
                            'detention', 'humanitarian', 'abuse', 'freedom', 'justice'],
            'international': ['international', 'foreign', 'relations', 'treaty',
                             'alliance', 'nato', 'un', 'sanctions', 'diplomacy'],
            'military': ['military', 'army', 'navy', 'defense', 'war', 'troops',
                        'weapons', 'attack', 'conflict', 'security'],
            'health': ['health', 'medical', 'vaccine', 'disease', 'hospital',
                      'treatment', 'pandemic', 'healthcare'],
            'environment': ['climate', 'environment', 'pollution', 'carbon',
                           'renewable', 'sustainability', 'emissions']
        }

        scores = {}
        for category, keywords in categories.items():
            score = sum(1 for kw in keywords if kw in topic_lower or kw in content)
            scores[category] = score

        # Return highest scoring category
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return 'general'

    def _extract_facts(self, articles: List[Dict], topic: str) -> List[str]:
        """Extract key facts from articles."""
        facts = []
        seen_facts = set()

        for article in articles:
            content = article.get('content', '') or article.get('snippet', '')

            # Split into sentences
            sentences = re.split(r'[.!?]+', content)

            for sentence in sentences:
                sentence = sentence.strip()

                # Filter for fact-like sentences
                if len(sentence) > 40 and len(sentence) < 300:
                    # Check if contains factual indicators
                    fact_indicators = [
                        r'\d{4}',  # Years
                        r'\d+%',   # Percentages
                        r'\$\d+',  # Dollar amounts
                        r'\d+ (million|billion|thousand)',  # Numbers
                        'said', 'announced', 'reported', 'according to',
                        'confirmed', 'stated', 'declared'
                    ]

                    if any(re.search(pattern, sentence, re.I) for pattern in fact_indicators):
                        # Normalize fact
                        fact = re.sub(r'\s+', ' ', sentence).strip()

                        # Check for duplicate
                        fact_key = fact.lower()[:100]
                        if fact_key not in seen_facts:
                            seen_facts.add(fact_key)
                            facts.append(fact)

        # Prioritize facts with topic keywords
        topic_words = set(topic.lower().split())
        scored_facts = []
        for fact in facts:
            score = sum(1 for word in topic_words if word in fact.lower())
            scored_facts.append((score, fact))

        scored_facts.sort(reverse=True)
        return [f[1] for f in scored_facts[:15]]

    def _build_timeline(self, articles: List[Dict], topic: str) -> List[Dict]:
        """Build chronological timeline of events."""
        events = []

        for article in articles:
            content = article.get('content', '') or article.get('snippet', '')

            # Find date patterns with context
            date_patterns = [
                r'(on\s+)?(\w+\s+\d{1,2},?\s+\d{4})',  # January 15, 2025
                r'(on\s+)?(\d{1,2}/\d{1,2}/\d{4})',    # 1/15/2025
                r'(last\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
                r'(yesterday|today|this week|last week)',
            ]

            for pattern in date_patterns:
                matches = re.finditer(pattern, content, re.I)
                for match in matches:
                    # Get context around date
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 150)
                    context = content[start:end].strip()

                    if len(context) > 50:
                        events.append({
                            'date': match.group(),
                            'description': context,
                            'source': article.get('domain', '')
                        })

        # Deduplicate and limit
        seen = set()
        unique_events = []
        for event in events:
            key = event['description'][:50]
            if key not in seen:
                seen.add(key)
                unique_events.append(event)

        return unique_events[:8]

    def _generate_summary(self, topic: str, facts: List[str], category: str) -> str:
        """Generate a summary of the research."""
        if not facts:
            return f"Research on: {topic}"

        # Use first 3 most relevant facts for summary
        summary_parts = facts[:3]
        summary = ' '.join(summary_parts)

        # Truncate if too long
        if len(summary) > 500:
            summary = summary[:497] + '...'

        return summary

    def _extract_image_keywords(self, topic: str, facts: List[str], category: str) -> List[str]:
        """Extract keywords suitable for image search."""
        keywords = []

        # Add topic words
        topic_words = topic.split()
        keywords.extend([w for w in topic_words if len(w) > 3])

        # Add category-specific visual keywords
        category_visuals = {
            'politics': ['government building', 'press conference', 'podium speech', 'capitol'],
            'economy': ['stock market', 'money', 'financial chart', 'business'],
            'technology': ['technology', 'digital', 'computer', 'innovation'],
            'military': ['military', 'soldiers', 'defense', 'security'],
            'human_rights': ['protest', 'people', 'crowd', 'justice'],
            'international': ['world map', 'diplomacy', 'flags', 'summit'],
            'health': ['hospital', 'medical', 'healthcare', 'doctor'],
            'environment': ['nature', 'climate', 'earth', 'green']
        }

        if category in category_visuals:
            keywords.extend(category_visuals[category])

        # Extract named entities from facts
        for fact in facts[:5]:
            # Find proper nouns (capitalized words)
            proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', fact)
            keywords.extend(proper_nouns[:2])

        # Deduplicate and limit
        seen = set()
        unique_keywords = []
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower not in seen and len(kw) > 2:
                seen.add(kw_lower)
                unique_keywords.append(kw)

        return unique_keywords[:15]

    def _find_related_topics(self, articles: List[Dict], topic: str) -> List[str]:
        """Find related topics mentioned in articles."""
        related = []
        topic_words = set(topic.lower().split())

        for article in articles:
            content = article.get('content', '') or article.get('snippet', '')

            # Find potential topic phrases (2-3 capitalized words together)
            phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b', content)

            for phrase in phrases:
                phrase_words = set(phrase.lower().split())
                # Only include if different from main topic
                if not phrase_words.intersection(topic_words):
                    related.append(phrase)

        # Count occurrences and return top ones
        from collections import Counter
        counts = Counter(related)
        return [item[0] for item in counts.most_common(5)]

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            return domain
        except Exception:
            return ""


if __name__ == "__main__":
    # Test the researcher
    researcher = WebResearcher()

    result = researcher.research_topic("Trump Venezuela president capture")

    print("\n" + "="*60)
    print("RESEARCH RESULTS")
    print("="*60)
    print(f"Topic: {result.topic}")
    print(f"Category: {result.category}")
    print(f"\nSummary: {result.summary[:200]}...")
    print(f"\nKey Facts ({len(result.key_facts)}):")
    for i, fact in enumerate(result.key_facts[:5], 1):
        print(f"  {i}. {fact[:100]}...")
    print(f"\nSources ({len(result.sources)}):")
    for source in result.sources[:5]:
        print(f"  - {source.title[:50]}... ({source.domain})")
    print(f"\nImage Keywords: {', '.join(result.image_keywords[:10])}")
