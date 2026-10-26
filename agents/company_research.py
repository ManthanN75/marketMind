"""Source-linked, repeatable public-company comparison for Capital Compass."""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any
from urllib.parse import quote

import pandas as pd
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import yfinance as yf


COMPANY_TICKERS = {
    "APPLE": "AAPL", "APPLE INC": "AAPL", "MICROSOFT": "MSFT",
    "TESLA": "TSLA", "AMAZON": "AMZN", "GOOGLE": "GOOGL",
    "ALPHABET": "GOOGL", "META": "META", "NVIDIA": "NVDA",
    "AMD": "AMD", "ADVANCED MICRO DEVICES": "AMD", "MCDONALDS": "MCD",
    "MCDONALD'S": "MCD", "TCS": "TCS.NS", "TATA CONSULTANCY SERVICES": "TCS.NS",
    "ITC": "ITC.NS", "VEDANTA": "VEDL.NS", "RELIANCE": "RELIANCE.NS",
    "RELIANCE INDUSTRIES": "RELIANCE.NS", "INFOSYS": "INFY.NS",
    "WIPRO": "WIPRO.NS", "HDFC BANK": "HDFCBANK.NS", "ICICI BANK": "ICICIBANK.NS",
    "SAMSUNG": "005930.KS", "SAMSUNG ELECTRONICS": "005930.KS",
    "LG": "066570.KS", "LG ELECTRONICS": "066570.KS",
    "TOYOTA": "7203.T", "TOYOTA MOTOR": "7203.T", "SONY": "6758.T",
    "SONY CORPORATION": "6758.T", "NINTENDO": "7974.T", "HONDA": "7267.T",
    "BYD": "1211.HK", "BYD COMPANY": "1211.HK", "VOLKSWAGEN": "VOW3.DE",
    "BMW": "BMW.DE", "MERCEDES": "MBG.DE", "SAP": "SAP.DE",
}

# Suggestions are starting points, not claims that businesses are identical.
PEER_SUGGESTIONS = {
    "AAPL": [("Samsung Electronics", "005930.KS", "competes in smartphones and consumer devices")],
    "005930.KS": [("Apple", "AAPL", "competes in smartphones and consumer devices")],
    "TSLA": [("BYD", "1211.HK", "competes in electric vehicles and batteries")],
    "1211.HK": [("Tesla", "TSLA", "competes in electric vehicles and batteries")],
    "NVDA": [("AMD", "AMD", "competes in GPUs and data-center accelerators")],
    "AMD": [("NVIDIA", "NVDA", "competes in GPUs and data-center accelerators")],
    "MSFT": [("Alphabet", "GOOGL", "overlaps in cloud, software, and AI products")],
    "GOOGL": [("Microsoft", "MSFT", "overlaps in cloud, software, and AI products")],
    "7203.T": [("Volkswagen", "VOW3.DE", "large global automaker; product and regional mix differ")],
    "TCS.NS": [("Infosys", "INFY.NS", "Indian IT services company with a similar services market")],
    "INFY.NS": [("TCS", "TCS.NS", "Indian IT services company with a similar services market")],
}

BENCHMARKS = {
    ".NS": ("NIFTY 50", "^NSEI"), ".BO": ("BSE SENSEX", "^BSESN"),
    ".T": ("Nikkei 225", "^N225"), ".KS": ("KOSPI", "^KS11"),
    ".DE": ("DAX", "^GDAXI"), ".L": ("FTSE 100", "^FTSE"),
    ".HK": ("Hang Seng", "^HSI"),
}

NEWS_URL = "https://news.google.com/rss/search"
TIME_PERIODS = {"1 month": 1, "3 months": 3, "6 months": 6, "1 year": 12, "3 years": 36, "5 years": 60}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _clean_symbol(value: str) -> str:
    return value.strip().upper()


def lookup_company(query: str) -> list[dict[str, str]]:
    """Find listed-company candidates without silently choosing an ambiguous name."""
    clean = query.strip()
    if not clean:
        return []
    alias_symbol = COMPANY_TICKERS.get(clean.upper())
    if alias_symbol:
        try:
            info = yf.Ticker(alias_symbol).get_info()
            return [{
                "symbol": alias_symbol,
                "name": info.get("longName") or info.get("shortName") or clean,
                "exchange": info.get("fullExchangeName") or info.get("exchange") or "",
            }]
        except Exception:
            return [{"symbol": alias_symbol, "name": clean, "exchange": ""}]

    # A ticker-like query is explicit enough to validate directly.
    if re.fullmatch(r"[A-Za-z0-9^][A-Za-z0-9.^=_-]{0,19}", clean) and ("." in clean or any(ch.isdigit() for ch in clean) or len(clean) <= 5):
        symbol = _clean_symbol(clean)
        try:
            info = yf.Ticker(symbol).get_info()
            if info and (info.get("longName") or info.get("shortName") or info.get("quoteType") == "EQUITY"):
                return [{"symbol": symbol, "name": info.get("longName") or info.get("shortName") or symbol,
                         "exchange": info.get("fullExchangeName") or info.get("exchange") or ""}]
        except Exception:
            return []
        return []

    try:
        search = yf.Search(clean, max_results=8, news_count=0, lists_count=0)
        candidates = []
        seen = set()
        for quote_item in getattr(search, "quotes", []) or []:
            if quote_item.get("quoteType") not in (None, "EQUITY"):
                continue
            symbol = quote_item.get("symbol")
            if not symbol or symbol in seen:
                continue
            seen.add(symbol)
            candidates.append({
                "symbol": symbol,
                "name": quote_item.get("longname") or quote_item.get("shortname") or symbol,
                "exchange": quote_item.get("exchDisp") or quote_item.get("exchange") or "",
            })
        return candidates
    except Exception as exc:
        print(f"Company search is unavailable: {exc}")
        return []


def select_company(query: str, input_fn=input, print_fn=print) -> dict[str, str] | None:
    candidates = lookup_company(query)
    if not candidates:
        print_fn(f"No listed-company match found for {query!r}. Try its Yahoo Finance ticker, such as AAPL or TCS.NS.")
        return None
    if len(candidates) == 1:
        item = candidates[0]
        print_fn(f"Matched: {item['name']} ({item['symbol']}){(' - ' + item['exchange']) if item['exchange'] else ''}")
        confirm = input_fn("Use this company? (Y/n): ").strip().lower()
        return item if confirm in ("", "y", "yes") else None

    print_fn("Select the correct listed company:")
    for index, item in enumerate(candidates, 1):
        print_fn(f"  {index}. {item['name']} ({item['symbol']}) - {item['exchange']}")
    choice = input_fn(f"Enter 1-{len(candidates)} or press Enter to cancel: ").strip()
    if not choice.isdigit() or not 1 <= int(choice) <= len(candidates):
        return None
    return candidates[int(choice) - 1]


def suggest_peers(company: dict[str, str]) -> list[dict[str, str]]:
    return [{"name": name, "symbol": symbol, "reason": reason}
            for name, symbol, reason in PEER_SUGGESTIONS.get(company["symbol"], [])]


def _benchmark_for(symbol: str) -> tuple[str, str]:
    upper = symbol.upper()
    for suffix, benchmark in BENCHMARKS.items():
        if upper.endswith(suffix):
            return benchmark
    return "S&P 500", "^GSPC"


def _series_from_history(history: pd.DataFrame) -> pd.Series:
    if history is None or history.empty:
        return pd.Series(dtype=float)
    if isinstance(history.columns, pd.MultiIndex):
        history.columns = history.columns.get_level_values(0)
    if "Close" not in history.columns:
        return pd.Series(dtype=float)
    series = pd.to_numeric(history["Close"], errors="coerce").dropna()
    if series.empty:
        return series
    if getattr(series.index, "tz", None) is not None:
        series.index = series.index.tz_localize(None)
    return series.sort_index()


def _price_performance(series: pd.Series) -> dict[str, Any]:
    result = {}
    if series.empty:
        return result
    latest = float(series.iloc[-1])
    latest_date = series.index[-1].strftime("%Y-%m-%d")
    for label, months in TIME_PERIODS.items():
        target = series.index[-1] - pd.DateOffset(months=months)
        available = series.loc[series.index <= target]
        if available.empty:
            result[label] = None
        else:
            initial = float(available.iloc[-1])
            result[label] = round((latest / initial - 1) * 100, 2) if initial else None
    daily_returns = series.pct_change().dropna()
    volatility = float(daily_returns.std() * (252 ** 0.5) * 100) if len(daily_returns) > 1 else None
    running_max = series.cummax()
    drawdown = (series / running_max) - 1
    return {
        "last_close": round(latest, 4),
        "last_close_date": latest_date,
        "currency": "",
        "returns_percent": result,
        "annualized_volatility_percent": round(volatility, 2) if volatility is not None else None,
        "max_drawdown_percent": round(float(drawdown.min()) * 100, 2),
        "history": [{"date": idx.strftime("%Y-%m-%d"), "close": round(float(value), 4)}
                    for idx, value in series.resample("ME").last().dropna().items()],
        "history_interval": "month-end sample of daily auto-adjusted close",
    }


def _statement_value(frame: pd.DataFrame, labels: tuple[str, ...], column: Any) -> float | None:
    if frame is None or frame.empty:
        return None
    normalized = {str(index).strip().lower(): index for index in frame.index}
    for label in labels:
        if label.lower() in normalized:
            value = frame.loc[normalized[label.lower()], column]
            return float(value) if pd.notna(value) else None
    for wanted in labels:
        for key, original in normalized.items():
            if wanted.lower() in key:
                value = frame.loc[original, column]
                return float(value) if pd.notna(value) else None
    return None


def _annual_financials(ticker: yf.Ticker) -> list[dict[str, Any]]:
    try:
        income = ticker.income_stmt
        cash_flow = ticker.cashflow
    except Exception:
        return []
    if income is None or income.empty:
        return []
    periods = list(income.columns[:4])
    rows = []
    for period in periods:
        period_label = period.strftime("%Y") if hasattr(period, "strftime") else str(period)[:4]
        rows.append({
            "period": period_label,
            "revenue": _statement_value(income, ("Total Revenue", "Operating Revenue"), period),
            "net_income": _statement_value(income, ("Net Income", "Net Income Common Stockholders"), period),
            "research_and_development": _statement_value(income, ("Research And Development", "Research Development"), period),
            "capital_expenditure": _statement_value(cash_flow, ("Capital Expenditure", "Capital Expenditures"), period),
        })
    return rows


def fetch_company_snapshot(candidate: dict[str, str]) -> dict[str, Any]:
    """Fetch fundamentals and five years of monthly, adjusted prices."""
    symbol = candidate["symbol"]
    ticker = yf.Ticker(symbol)
    info = ticker.get_info()
    display_name = info.get("longName") or info.get("shortName") or candidate["name"]
    history = _series_from_history(ticker.history(period="5y", interval="1d", auto_adjust=True))
    if history.empty:
        raise ValueError(f"No historical price data was returned for {symbol}.")

    price_metrics = _price_performance(history)
    price_metrics["currency"] = info.get("currency", "")
    benchmark_name, benchmark_symbol = _benchmark_for(symbol)
    benchmark_history = _series_from_history(yf.Ticker(benchmark_symbol).history(
        period="5y", interval="1d", auto_adjust=True
    ))
    benchmark_metrics = _price_performance(benchmark_history)
    revenue = info.get("totalRevenue")
    summary = info.get("longBusinessSummary") or "Company profile summary is not available from the selected data source."
    return {
        "name": display_name,
        "symbol": symbol,
        "exchange": info.get("fullExchangeName") or candidate.get("exchange") or info.get("exchange"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "business_summary": summary,
        "market_cap": info.get("marketCap"),
        "currency": info.get("currency"),
        "price": info.get("currentPrice") or info.get("regularMarketPrice") or price_metrics.get("last_close"),
        "price_date": price_metrics.get("last_close_date"),
        "valuation": {
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "price_to_book": info.get("priceToBook"),
            "enterprise_value_to_ebitda": info.get("enterpriseToEbitda"),
        },
        "operating_metrics": {
            "revenue": revenue,
            "revenue_growth_percent": _as_percent(info.get("revenueGrowth")),
            "earnings_growth_percent": _as_percent(info.get("earningsGrowth")),
            "profit_margin_percent": _as_percent(info.get("profitMargins")),
            "return_on_equity_percent": _as_percent(info.get("returnOnEquity")),
        },
        "annual_financials": _annual_financials(ticker),
        "share_performance": price_metrics,
        "benchmark": {"name": benchmark_name, "symbol": benchmark_symbol, "performance": benchmark_metrics},
        "source": {
            "name": "Yahoo Finance",
            "url": f"https://finance.yahoo.com/quote/{quote(symbol, safe='.^=')}/",
            "annual_financials_url": f"https://finance.yahoo.com/quote/{quote(symbol, safe='.^=')}/financials/",
            "retrieved_at": _utc_now().isoformat(),
            "price_history_method": "yfinance daily auto-adjusted close; returns use the nearest available close on or before each period start",
        },
    }


def _as_percent(value: Any) -> float | None:
    try:
        return round(float(value) * 100, 2) if value is not None else None
    except (TypeError, ValueError):
        return None


def fetch_news(company: dict[str, str], limit: int = 15) -> dict[str, Any]:
    """Fetch dated Google News RSS headlines and attach a transparent text score."""
    query_name = company["name"]
    params = {"q": f'"{query_name}" when:3m', "hl": "en-US", "gl": "US", "ceid": "US:en"}
    response = requests.get(NEWS_URL, params=params, timeout=20, headers={"User-Agent": "CapitalCompass/1.0 research-bot"})
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "xml")
    articles = []
    for item in soup.find_all("item")[:limit]:
        title = item.title.get_text(" ", strip=True) if item.title else "Untitled"
        link = item.link.get_text(strip=True) if item.link else ""
        pub_date = item.pubDate.get_text(strip=True) if item.pubDate else None
        source = item.find("source")
        description = ""
        if item.description:
            description = BeautifulSoup(item.description.get_text(), "html.parser").get_text(" ", strip=True)
        polarity = round(TextBlob(f"{title}. {description}").sentiment.polarity, 3)
        articles.append({
            "title": title,
            "published_at": pub_date,
            "publisher": source.get_text(" ", strip=True) if source else "Google News",
            "link": link,
            "description": description[:500],
            "news_tone_score": polarity,
            "news_tone": "positive" if polarity > 0.1 else "negative" if polarity < -0.1 else "neutral",
            "source": "Google News RSS",
        })
    values = [item["news_tone_score"] for item in articles]
    mean_score = round(sum(values) / len(values), 3) if values else None
    return {
        "query": query_name,
        "window": "Google News search filtered to the past three months",
        "articles": articles,
        "article_count": len(articles),
        "average_news_tone_score": mean_score,
        "source": {"name": "Google News RSS", "url": response.url, "retrieved_at": _utc_now().isoformat()},
    }


EVENT_TERMS = {
    "Legal / litigation": ("lawsuit", "sued", "court", "litigation", "class action", "settlement", "infringement"),
    "Regulatory / investigation": ("investigation", "regulator", "antitrust", "probe", "fine", "sanction", "regulatory"),
    "Safety / recall": ("recall", "safety issue", "defect", "injury", "fatal", "nhtsa"),
    "Data / privacy": ("data breach", "privacy breach", "cyberattack", "ransomware", "data leak"),
    "Public controversy": ("boycott", "controversy", "misconduct", "allegation", "accused", "protest"),
}


def identify_events(news: dict[str, Any]) -> list[dict[str, Any]]:
    events = []
    for article in news.get("articles", []):
        text = f"{article.get('title', '')} {article.get('description', '')}".casefold()
        categories = [category for category, terms in EVENT_TERMS.items() if any(term in text for term in terms)]
        if categories:
            events.append({
                "categories": categories,
                "headline": article.get("title"),
                "published_at": article.get("published_at"),
                "publisher": article.get("publisher"),
                "link": article.get("link"),
                "interpretation": "Headline keyword match only. Open the linked source to verify the event, its status, and the company's response.",
            })
    return events


def _candidate_from_peer_text(query: str, input_fn=input, print_fn=print) -> dict[str, str] | None:
    return select_company(query, input_fn=input_fn, print_fn=print_fn)


class CompanyResearchPipeline:
    """Collect a comparable, source-linked company brief without requiring Gemini."""

    def __init__(self, output_root: str = "data/runs", report_root: str = "reports"):
        self.output_root = output_root
        self.report_root = report_root

    def run(self, primary: dict[str, str], peer: dict[str, str] | None = None) -> dict[str, Any]:
        import json
        import os
        import re as _re

        from agents.capital_compass_report import ReportWriterAgent

        started = _utc_now()
        print(f"\n=== Capital Compass: {primary['name']} ({primary['symbol']}) ===")
        print("Fetching company fundamentals and historical prices...")
        companies = []
        for candidate in [primary] + ([peer] if peer else []):
            try:
                companies.append(fetch_company_snapshot(candidate))
            except Exception as exc:
                print(f"Could not fetch financial profile for {candidate['symbol']}: {exc}")
                if candidate["symbol"] == primary["symbol"]:
                    raise
                peer = None
        print("Fetching recent company news...")
        news_by_symbol = {}
        events_by_symbol = {}
        for company in companies:
            try:
                news = fetch_news({"name": company["name"], "symbol": company["symbol"]})
            except Exception as exc:
                news = {"articles": [], "article_count": 0, "average_news_tone_score": None,
                        "error": str(exc), "source": {"name": "Google News RSS", "retrieved_at": _utc_now().isoformat()}}
                print(f"News unavailable for {company['name']}: {exc}")
            news_by_symbol[company["symbol"]] = news
            events_by_symbol[company["symbol"]] = identify_events(news)

        peer_suggestion = suggest_peers(primary)
        result = {
            "product": "Capital Compass",
            "run_id": started.strftime("%Y%m%dT%H%M%SZ"),
            "generated_at": started.isoformat(),
            "coverage_note": "Public-company coverage depends on Yahoo Finance data availability. Headline tone is a text heuristic, not a measure of all public opinion.",
            "companies": companies,
            "news_by_symbol": news_by_symbol,
            "recent_events_by_symbol": events_by_symbol,
            "peer_suggestion": peer_suggestion[0] if peer_suggestion else None,
            "methodology": {
                "price_returns": "Calculated from daily auto-adjusted closes using the closest observation on or before the period start.",
                "annualized_volatility": "Standard deviation of daily adjusted-price returns multiplied by square root of 252 trading days.",
                "maximum_drawdown": "Largest peak-to-trough decline in the available daily adjusted-price series.",
                "news_tone": "TextBlob polarity on retrieved headline and RSS description; it can miss context and is not investment advice.",
                "event_flags": "Keyword matches used to surface articles for human review; not confirmation that an allegation is true.",
            },
        }

        slug = _re.sub(r"[^A-Za-z0-9-]+", "-", primary["symbol"]).strip("-").lower() or "company"
        run_dir = os.path.join(self.output_root, f"{slug}_{result['run_id']}")
        os.makedirs(run_dir, exist_ok=True)
        data_path = os.path.join(run_dir, "capital_compass_report.json")
        with open(data_path, "w", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, ensure_ascii=False, default=str)

        os.makedirs(self.report_root, exist_ok=True)
        pdf_path = os.path.join(self.report_root, f"{slug}_{result['run_id']}_capital_compass.pdf")
        ReportWriterAgent(report_data=result, output_path=pdf_path).generate_report()
        print(f"Saved evidence data: {data_path}")
        print(f"Saved report: {pdf_path}")
        return result


def choose_peer(primary: dict[str, str], input_fn=input, print_fn=print) -> dict[str, str] | None:
    suggestions = suggest_peers(primary)
    if suggestions:
        print_fn("\nSuggested competitor:")
        for index, peer in enumerate(suggestions, 1):
            print_fn(f"  {index}. {peer['name']} ({peer['symbol']}) - {peer['reason']}")
    prompt = "Enter a different competitor name/ticker, press Enter for the suggestion, or type 'skip': "
    answer = input_fn(prompt).strip()
    if answer.casefold() == "skip":
        return None
    if not answer and suggestions:
        return {"name": suggestions[0]["name"], "symbol": suggestions[0]["symbol"]}
    if not answer:
        return None
    return _candidate_from_peer_text(answer, input_fn, print_fn)
