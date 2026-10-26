"""Produce the source-linked Capital Compass company comparison PDF."""

from datetime import datetime
import html
import os
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class ReportWriterAgent:
    """Write a compact company brief from an explicit data snapshot."""

    def __init__(self, report_data, output_path):
        self.report_data = report_data
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self._define_styles()

    def _define_styles(self):
        self.styles.add(ParagraphStyle(
            name="CCTitle", parent=self.styles["Title"], fontName="Helvetica-Bold",
            fontSize=25, leading=30, textColor=colors.HexColor("#102A43"),
            alignment=TA_CENTER, spaceAfter=6,
        ))
        self.styles.add(ParagraphStyle(
            name="CCSubtitle", parent=self.styles["Normal"], fontSize=9,
            leading=13, alignment=TA_CENTER, textColor=colors.HexColor("#627D98"),
        ))
        self.styles.add(ParagraphStyle(
            name="CCSection", parent=self.styles["Heading1"], fontName="Helvetica-Bold",
            fontSize=14, leading=18, textColor=colors.HexColor("#102A43"),
            spaceBefore=11, spaceAfter=6, keepWithNext=True,
        ))
        self.styles.add(ParagraphStyle(
            name="CCSubsection", parent=self.styles["Heading2"], fontName="Helvetica-Bold",
            fontSize=10, leading=13, textColor=colors.HexColor("#334E68"),
            spaceBefore=6, spaceAfter=4, keepWithNext=True,
        ))
        self.styles.add(ParagraphStyle(
            name="CCBody", parent=self.styles["BodyText"], fontSize=8.5,
            leading=12, textColor=colors.HexColor("#243B53"), spaceAfter=4,
        ))
        self.styles.add(ParagraphStyle(
            name="CCSmall", parent=self.styles["BodyText"], fontSize=7.5,
            leading=10, textColor=colors.HexColor("#627D98"), spaceAfter=3,
        ))
        self.styles.add(ParagraphStyle(
            name="CCWarning", parent=self.styles["BodyText"], fontSize=8.5,
            leading=12, textColor=colors.HexColor("#9A3412"),
        ))

    @staticmethod
    def _p(value, style):
        return Paragraph(escape(str(value or "Not available")), style)

    @staticmethod
    def _fmt(value, digits=2):
        try:
            return f"{float(value):,.{digits}f}"
        except (TypeError, ValueError):
            return "Not available"

    @staticmethod
    def _money(value, currency=""):
        if value is None:
            return "Not available"
        try:
            amount = float(value)
        except (TypeError, ValueError):
            return "Not available"
        for threshold, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
            if abs(amount) >= threshold:
                return f"{currency} {amount / threshold:.2f}{suffix}".strip()
        return f"{currency} {amount:,.0f}".strip()

    def _table(self, rows, widths=None, repeat_rows=1):
        table = Table(rows, colWidths=widths, repeatRows=repeat_rows, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#102A43")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("LEADING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F4F8")]),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9E2EC")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        return table

    def _header(self, primary):
        peer = self.report_data["companies"][1] if len(self.report_data["companies"]) > 1 else None
        subtitle = f"{primary['symbol']} | {primary.get('exchange') or 'Exchange not listed'}"
        if peer:
            subtitle += f"  vs  {peer['name']} ({peer['symbol']})"
        return [
            Spacer(1, 0.18 * inch),
            Paragraph("CAPITAL COMPASS", self.styles["CCSubtitle"]),
            Paragraph("Company Research Brief", self.styles["CCTitle"]),
            Paragraph(escape(primary["name"]) + "<br/>" + escape(subtitle), self.styles["CCSubtitle"]),
            Spacer(1, 0.1 * inch),
            HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#2F80ED")),
            Spacer(1, 0.12 * inch),
            Paragraph(f"Prepared {datetime.now().strftime('%d %b %Y, %H:%M')} | Run {escape(self.report_data['run_id'])}", self.styles["CCSmall"]),
        ]

    def _comparison(self, companies):
        labels = ["Metric", companies[0]["name"]]
        if len(companies) > 1:
            labels.append(companies[1]["name"])
        rows = [labels]
        metrics = [
            ("Share price", lambda c: f"{c.get('currency') or ''} {self._fmt(c.get('price'))}".strip()),
            ("Market capitalization", lambda c: self._money(c.get("market_cap"), c.get("currency"))),
            ("Revenue growth", lambda c: self._percent(c.get("operating_metrics", {}).get("revenue_growth_percent"))),
            ("Earnings growth", lambda c: self._percent(c.get("operating_metrics", {}).get("earnings_growth_percent"))),
            ("Profit margin", lambda c: self._percent(c.get("operating_metrics", {}).get("profit_margin_percent"))),
            ("Return on equity", lambda c: self._percent(c.get("operating_metrics", {}).get("return_on_equity_percent"))),
            ("Trailing P/E", lambda c: self._fmt(c.get("valuation", {}).get("trailing_pe"))),
            ("Forward P/E", lambda c: self._fmt(c.get("valuation", {}).get("forward_pe"))),
            ("Price / book", lambda c: self._fmt(c.get("valuation", {}).get("price_to_book"))),
            ("Enterprise value / EBITDA", lambda c: self._fmt(c.get("valuation", {}).get("enterprise_value_to_ebitda"))),
        ]
        for label, getter in metrics:
            rows.append([label] + [getter(company) for company in companies])
        widths = [2.05*inch] + ([2.45*inch] * (len(companies)))
        section = [Paragraph("At a glance", self.styles["CCSection"]), self._table(rows, widths)]
        section.append(Paragraph(
            "Valuation ratios are context, not a verdict: companies in different industries or with different growth profiles may not be directly comparable.",
            self.styles["CCSmall"],
        ))
        return section

    @staticmethod
    def _percent(value):
        return f"{ReportWriterAgent._fmt(value)}%" if value is not None else "Not available"

    def _performance(self, companies):
        rows = [["Period", *[company["name"] for company in companies]]]
        primary = companies[0]
        benchmark = primary.get("benchmark", {})
        for period in ("1 month", "3 months", "6 months", "1 year", "3 years", "5 years"):
            values = []
            for company in companies:
                returns = company.get("share_performance", {}).get("returns_percent", {})
                value = returns.get(period)
                values.append(self._percent(value))
            rows.append([period, *values])
        benchmark_name = benchmark.get("name")
        if benchmark_name:
            benchmark_returns = benchmark.get("performance", {}).get("returns_percent", {})
            rows = [rows[0] + [benchmark_name]] + [row + [self._percent(benchmark_returns.get(row[0]))] for row in rows[1:]]
        widths = [1.65*inch] + [4.95*inch / (len(rows[0]) - 1)] * (len(rows[0]) - 1)
        section = [
            Paragraph("Share performance", self.styles["CCSection"]),
            self._table(rows, widths),
        ]
        risk_rows = [["Risk measure", *[company["name"] for company in companies]]]
        for label, key in (("Annualized volatility", "annualized_volatility_percent"),
                           ("Maximum drawdown", "max_drawdown_percent")):
            risk_rows.append([label] + [self._percent(company.get("share_performance", {}).get(key)) for company in companies])
        section.extend([
            Spacer(1, 4),
            self._table(risk_rows, [1.65*inch] + [4.95*inch / len(companies)] * len(companies)),
            Paragraph(
                "Returns use daily auto-adjusted closing prices. Volatility is annualized from daily returns; drawdown uses the daily price path. "
                "The benchmark is selected from the company's listing suffix; cross-market comparisons use percentage returns. Latest close: "
                + escape(str(primary.get("price_date") or "date unavailable")) + ".",
                self.styles["CCSmall"],
            ),
        ])
        return section

    def _company_profiles(self, companies):
        elements = [Paragraph("What these companies do", self.styles["CCSection"])]
        for company in companies:
            profile = company.get("business_summary") or "No company profile was provided by the data source."
            if len(profile) > 950:
                profile = profile[:947].rsplit(" ", 1)[0] + "..."
            elements.append(Paragraph(
                f"<b>{escape(company['name'])}</b> - {escape(str(company.get('sector') or 'Sector not listed'))} / "
                f"{escape(str(company.get('industry') or 'Industry not listed'))}", self.styles["CCSubsection"]
            ))
            elements.append(Paragraph(escape(profile), self.styles["CCBody"]))
            elements.append(Paragraph(
                f"Profile source: <link href=\"{html.escape(company['source']['url'], quote=True)}\" color=\"#1769AA\">Yahoo Finance company page</link>",
                self.styles["CCSmall"],
            ))
        return elements

    def _investment(self, companies):
        elements = [Paragraph("Investment in technology and growth", self.styles["CCSection"])]
        for company in companies:
            rows = [["Fiscal period", "R&D expense", "Capital expenditure"]]
            annual = company.get("annual_financials", [])
            for item in annual[:4]:
                rows.append([
                    str(item.get("period", "Not available")),
                    self._money(item.get("research_and_development"), company.get("currency")),
                    self._money(abs(item["capital_expenditure"]) if item.get("capital_expenditure") is not None else None, company.get("currency")),
                ])
            elements.append(Paragraph(escape(company["name"]), self.styles["CCSubsection"]))
            if len(rows) > 1:
                elements.append(self._table(rows, [1.6*inch, 2.45*inch, 2.55*inch]))
            else:
                elements.append(Paragraph("Annual R&D and capital-expenditure data is not available from the selected feed.", self.styles["CCBody"]))
        elements.append(Paragraph(
            "R&D is used as a broad indicator of research investment; it may include non-technology research. Capital expenditure covers assets across the business, not technology alone. Fiscal years and reporting practices can differ.",
            self.styles["CCSmall"],
        ))
        return elements

    def _news_and_events(self, companies):
        elements = [Paragraph("Recent news, tone, and events to review", self.styles["CCSection"])]
        news_map = self.report_data.get("news_by_symbol", {})
        events_map = self.report_data.get("recent_events_by_symbol", {})
        for company in companies:
            news = news_map.get(company["symbol"], {})
            elements.append(Paragraph(escape(company["name"]), self.styles["CCSubsection"]))
            score = news.get("average_news_tone_score")
            tone = "not available" if score is None else f"{self._fmt(score, 3)} average headline tone ({'positive' if score > 0.1 else 'negative' if score < -0.1 else 'neutral'})"
            elements.append(Paragraph(
                f"{news.get('article_count', 0)} articles retrieved; {escape(tone)}. "
                "Headline tone is an automated text estimate, not public-opinion polling.", self.styles["CCSmall"]
            ))
            rows = [["Headline / publisher", "Published", "Tone"]]
            for article in news.get("articles", [])[:7]:
                title = str(article.get("title", "Untitled"))
                link = str(article.get("link", ""))
                linked_title = escape(title)
                if link.startswith(("https://", "http://")):
                    linked_title = f'<link href="{html.escape(link, quote=True)}" color="#1769AA">{linked_title}</link>'
                rows.append([
                    Paragraph(f"{linked_title}<br/><font color='#627D98'>{escape(str(article.get('publisher') or 'Publisher not listed'))}</font>", self.styles["CCBody"]),
                    Paragraph(escape(str(article.get("published_at") or "Date unavailable")), self.styles["CCSmall"]),
                    escape(f"{article.get('news_tone_score', 'n/a')} ({article.get('news_tone', 'not scored')})"),
                ])
            if len(rows) > 1:
                elements.append(self._table(rows, [4.2*inch, 1.45*inch, 1.0*inch]))
            else:
                elements.append(Paragraph("No articles were retrieved for this company.", self.styles["CCBody"]))
            events = events_map.get(company["symbol"], [])
            elements.append(Paragraph("Events surfaced for human review", self.styles["CCSubsection"]))
            if events:
                for event in events[:6]:
                    categories = ", ".join(event.get("categories", []))
                    title = str(event.get("headline") or "Untitled")
                    link = str(event.get("link") or "")
                    label = escape(title)
                    if link.startswith(("https://", "http://")):
                        label = f'<link href="{html.escape(link, quote=True)}" color="#1769AA">{label}</link>'
                    elements.append(Paragraph(
                        f"- <b>{escape(categories)}</b>: {label} ({escape(str(event.get('published_at') or 'date unavailable'))}). "
                        "Headline match only; verify the linked reporting and company response.", self.styles["CCBody"]
                    ))
            else:
                elements.append(Paragraph("No matching event headlines were found in the retrieved feed. This does not establish that no events exist.", self.styles["CCSmall"]))
        return elements

    def _sources_and_method(self):
        elements = [Paragraph("Sources and how to read this brief", self.styles["CCSection"])]
        for company in self.report_data.get("companies", []):
            source = company.get("source", {})
            elements.append(Paragraph(
                f"{escape(company['name'])} financial data: <link href=\"{html.escape(source.get('url', ''), quote=True)}\" color=\"#1769AA\">Yahoo Finance</link>. "
                f"Retrieved {escape(str(source.get('retrieved_at') or 'timestamp unavailable'))}.", self.styles["CCSmall"]
            ))
            if source.get("annual_financials_url"):
                elements.append(Paragraph(
                    f"{escape(company['name'])} annual statements: <link href=\"{html.escape(source['annual_financials_url'], quote=True)}\" color=\"#1769AA\">Yahoo Finance financials</link>.",
                    self.styles["CCSmall"],
                ))
        for news in self.report_data.get("news_by_symbol", {}).values():
            source = news.get("source", {})
            if source.get("url"):
                elements.append(Paragraph(
                    f"News search: <link href=\"{html.escape(source['url'], quote=True)}\" color=\"#1769AA\">Google News RSS query</link>. "
                    f"Retrieved {escape(str(source.get('retrieved_at') or 'timestamp unavailable'))}.", self.styles["CCSmall"]
                ))
        elements.append(Paragraph(escape(self.report_data.get("coverage_note", "")), self.styles["CCSmall"]))
        elements.append(Paragraph(escape(self.report_data.get("methodology", {}).get("price_returns", "")), self.styles["CCSmall"]))
        elements.append(Paragraph(
            "For research and education only. Not investment advice. Data may be delayed, incomplete, or revised by its provider.",
            self.styles["CCSmall"],
        ))
        return elements

    def _footer(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D9E2EC"))
        canvas.line(0.62*inch, 0.53*inch, 7.88*inch, 0.53*inch)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#627D98"))
        canvas.drawString(0.65*inch, 0.34*inch, "Capital Compass | Informational use only")
        canvas.drawRightString(7.85*inch, 0.34*inch, f"Page {doc.page}")
        canvas.restoreState()

    def generate_report(self):
        os.makedirs(os.path.dirname(self.output_path) or ".", exist_ok=True)
        companies = self.report_data.get("companies", [])
        if not companies:
            raise ValueError("No company data is available to report.")
        doc = SimpleDocTemplate(
            self.output_path, pagesize=letter,
            rightMargin=0.62*inch, leftMargin=0.62*inch,
            topMargin=0.52*inch, bottomMargin=0.68*inch,
            title=f"Capital Compass - {companies[0]['name']}", author="Capital Compass",
        )
        story = self._header(companies[0])
        story.extend(self._comparison(companies))
        story.extend(self._performance(companies))
        story.extend(self._company_profiles(companies))
        story.extend(self._investment(companies))
        story.extend(self._news_and_events(companies))
        story.extend(self._sources_and_method())
        doc.build(story, onFirstPage=self._footer, onLaterPages=self._footer)
        print(f"Capital Compass report generated: {self.output_path}")
        return self.output_path
