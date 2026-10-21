"""Build a readable PDF report from the market analysis JSON files."""

from datetime import datetime
import html
import json
import os
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class ReportWriterAgent:
    """Create a PDF that shows source data and calls out missing analysis."""

    def __init__(self, company, input_dir="data", output_dir="reports"):
        self.company = company
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name="ReportTitle", parent=self.styles["Title"], fontName="Helvetica-Bold",
            fontSize=25, leading=30, textColor=colors.HexColor("#102A43"),
            alignment=TA_CENTER, spaceAfter=8,
        ))
        self.styles.add(ParagraphStyle(
            name="Subtitle", parent=self.styles["Normal"], fontSize=10,
            leading=14, textColor=colors.HexColor("#52606D"), alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            name="SectionHeader", parent=self.styles["Heading1"], fontName="Helvetica-Bold",
            fontSize=15, leading=19, textColor=colors.HexColor("#102A43"),
            spaceBefore=12, spaceAfter=7, keepWithNext=True,
        ))
        self.styles.add(ParagraphStyle(
            name="SubHeader", parent=self.styles["Heading2"], fontName="Helvetica-Bold",
            fontSize=11, leading=14, textColor=colors.HexColor("#334E68"),
            spaceBefore=7, spaceAfter=4, keepWithNext=True,
        ))
        self.styles.add(ParagraphStyle(
            name="BodySmall", parent=self.styles["BodyText"], fontSize=9,
            leading=13, textColor=colors.HexColor("#243B53"), spaceAfter=5,
        ))
        self.styles.add(ParagraphStyle(
            name="Muted", parent=self.styles["BodyText"], fontSize=8,
            leading=11, textColor=colors.HexColor("#627D98"), spaceAfter=4,
        ))
        self.styles.add(ParagraphStyle(
            name="Callout", parent=self.styles["BodyText"], fontSize=9,
            leading=13, textColor=colors.HexColor("#7C2D12"),
        ))

    def _load_data(self):
        data = {}
        for key, filename in {
            "research": "raw_data.json",
            "financial": "financial_data.json",
            "sentiment": "sentiment_data.json",
            "analysis": "analysis_data.json",
            "regulatory": "regulatory_data.json",
        }.items():
            try:
                with open(os.path.join(self.input_dir, filename), "r", encoding="utf-8") as stream:
                    data[key] = json.load(stream)
            except (OSError, json.JSONDecodeError) as exc:
                print(f"Warning: Could not load {filename}: {exc}")
                data[key] = {}
        return data

    @staticmethod
    def _safe(value):
        return escape(str(value))

    @staticmethod
    def _number(value, digits=2):
        try:
            return f"{float(value):,.{digits}f}"
        except (TypeError, ValueError):
            return "Not available"

    def _company_name(self, data):
        for key in ("financial", "research", "sentiment", "analysis"):
            name = data.get(key, {}).get("company")
            if name:
                return name
        return self.company

    def _header(self, company, financial):
        ticker = financial.get("ticker")
        label = f"{company} ({ticker})" if ticker else company
        return [
            Spacer(1, 0.3 * inch),
            Paragraph("MarketMind", self.styles["Subtitle"]),
            Paragraph(f"Market Analysis: {self._safe(label)}", self.styles["ReportTitle"]),
            Paragraph(
                f"Generated {datetime.now().strftime('%d %b %Y, %H:%M')} | "
                f"Requested company: {self._safe(self.company)}",
                self.styles["Subtitle"],
            ),
            Spacer(1, 0.12 * inch),
            HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#2F80ED")),
            Spacer(1, 0.18 * inch),
        ]

    def _table(self, rows, widths=None):
        table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#102A43")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("LEADING", (0, 0), (-1, -1), 11),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F4F8")]),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9E2EC")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return table

    def _overview(self, data, company):
        financial = data.get("financial", {})
        research = data.get("research", {})
        sentiment = data.get("sentiment", {}).get("sentiment_analysis", {})
        news = research.get("news", [])
        articles = sentiment.get("news_sentiment", {}).get("articles", [])
        if not articles and isinstance(sentiment.get("news_sentiment"), dict):
            articles = sentiment["news_sentiment"].get("articles", [])
        scores = [a.get("sentiment_score") for a in articles if isinstance(a.get("sentiment_score"), (int, float))]
        score = sentiment.get("overall_score")
        if not isinstance(score, (int, float)) and scores:
            score = sum(scores) / len(scores)
        label = "unavailable"
        if isinstance(score, (int, float)):
            label = "positive" if score > 0.1 else "negative" if score < -0.1 else "neutral"
        price = financial.get("current_price")
        currency = financial.get("market_cap", {}).get("currency", "")
        price_label = f"{currency} {self._number(price)}".strip() if price is not None else "Not available"
        change = financial.get("price_change_percent")
        change_label = f"{self._number(change)}%" if change is not None else "Not available"
        market_cap = financial.get("market_cap", {}).get("formatted", "Not available")
        rows = [
            ["Snapshot", "Observed value", "Snapshot", "Observed value"],
            ["Share price", price_label, "Daily change", change_label],
            ["Market capitalization", market_cap, "Exchange", financial.get("exchange", "Not available")],
            ["52-week range", f"{self._number(financial.get('52_week_low'))} - {self._number(financial.get('52_week_high'))}", "P/E ratio", self._number(financial.get("pe_ratio"))],
            ["News articles", str(research.get("total_articles", len(news))), "News tone", f"{label} ({self._number(score, 3) if score is not None else 'n/a'})"],
        ]
        story = []
        if company.casefold() != str(self.company).casefold():
            story.append(Paragraph(
                f"Data mismatch: this report was requested as {self._safe(self.company)}, "
                f"but the saved data belongs to {self._safe(company)}. The metrics below are "
                "shown for the saved data company; rerun the analysis for the requested company.",
                self.styles["Callout"],
            ))
            story.append(Spacer(1, 6))
        story += [Paragraph("Executive snapshot", self.styles["SectionHeader"]), self._table(rows, [1.25*inch, 1.6*inch, 1.25*inch, 2.0*inch])]
        story.append(Spacer(1, 5))
        stamp = financial.get("timestamp") or research.get("timestamp") or "Not recorded"
        sources = ", ".join(research.get("sources_used", [])) or "Not recorded"
        story.append(Paragraph(f"Data timestamp: {self._safe(stamp)} | News source(s): {self._safe(sources)}", self.styles["Muted"]))
        return story

    def _news(self, data):
        research = data.get("research", {})
        sentiment = data.get("sentiment", {}).get("sentiment_analysis", {}).get("news_sentiment", {})
        articles = sentiment.get("articles", []) if isinstance(sentiment, dict) else []
        by_title = {str(a.get("title", "")).casefold(): a for a in articles}
        news = research.get("news", [])
        story = [Paragraph("News and sentiment", self.styles["SectionHeader"])]
        story.append(Paragraph(
            "Headlines are collected from the configured news feed. Sentiment is a lightweight "
            "headline-text estimate, not a prediction or a full-article reading.", self.styles["BodySmall"]
        ))
        rows = [["Headline / source", "Date", "Tone"]]
        for article in news[:10]:
            title = str(article.get("title") or "Untitled")
            url = str(article.get("link") or "")
            headline = self._safe(title)
            if url.startswith(("https://", "http://")):
                headline = f'<link href="{html.escape(url, quote=True)}" color="#1769AA">{headline}</link>'
            source = self._safe(article.get("source", "Source not listed"))
            score_data = by_title.get(title.casefold(), {})
            raw_score = score_data.get("sentiment_score")
            tone = "Not scored" if raw_score is None else f"{self._number(raw_score, 3)} ({'positive' if raw_score > 0.1 else 'negative' if raw_score < -0.1 else 'neutral'})"
            rows.append([Paragraph(f"{headline}<br/><font color='#627D98'>{source}</font>", self.styles["BodySmall"]),
                         Paragraph(self._safe(article.get("date", "Date not listed")), self.styles["Muted"]),
                         self._safe(tone)])
        if len(rows) == 1:
            story.append(Paragraph("No news articles were saved for this run.", self.styles["BodySmall"]))
        else:
            story.append(self._table(rows, [4.55*inch, 1.35*inch, 1.2*inch]))
        return story

    def _analysis(self, data):
        analysis = data.get("analysis", {})
        sentiment = data.get("sentiment", {}).get("sentiment_analysis", {})
        regulatory = data.get("regulatory", {})
        story = [Paragraph("Findings and risks", self.styles["SectionHeader"])]
        sections = [
            ("Market trends", analysis.get("market_trends", [])),
            ("Opportunities", analysis.get("opportunities", [])),
            ("Risk factors", analysis.get("risk_factors", [])),
            ("Competitor mentions", analysis.get("competitor_analysis", [])),
            ("Potential legal concerns", data.get("sentiment", {}).get("legal_concerns", [])),
            ("Regulatory mentions", regulatory.get("regulatory_mentions", [])),
            ("Compliance risks", regulatory.get("compliance_risks", [])),
        ]
        found = False
        for heading, items in sections:
            if not items:
                continue
            found = True
            story.append(Paragraph(self._safe(heading), self.styles["SubHeader"]))
            for item in items[:10]:
                if isinstance(item, dict):
                    desc = item.get("description") or item.get("title") or item.get("regulation") or json.dumps(item, ensure_ascii=True)
                    details = [f"{k}: {v}" for k, v in item.items() if k not in ("description", "title", "regulation", "link") and v not in (None, "")]
                    line = self._safe(desc)
                    if details:
                        line += f" <font color='#627D98'>({self._safe('; '.join(details))})</font>"
                    if str(item.get("link", "")).startswith(("https://", "http://")):
                        line += f" - <link href=\"{html.escape(item['link'], quote=True)}\" color=\"#1769AA\">source</link>"
                else:
                    line = self._safe(item)
                story.append(Paragraph(f"- {line}", self.styles["BodySmall"]))
        summary = sentiment.get("summary") or analysis.get("summary") or regulatory.get("summary")
        if summary:
            found = True
            story.append(Paragraph("Model summary", self.styles["SubHeader"]))
            story.append(Paragraph(self._safe(summary), self.styles["BodySmall"]))
        if not found:
            story.append(Paragraph(
                "No trend, opportunity, risk, competitor, or regulatory findings were produced in this run. "
                "The report shows the raw financial snapshot and news evidence above; it does not infer missing findings.",
                self.styles["Callout"],
            ))
        if sentiment.get("news_sentiment", {}).get("articles"):
            score = sentiment.get("news_sentiment", {}).get("overall_score")
            story.append(Paragraph(
                f"Calculated headline sentiment score: {self._number(score, 3)} on a scale from -1 (negative) to +1 (positive). "
                "This is a text heuristic and can miss context, sarcasm, and article details.", self.styles["Muted"]
            ))
        return story

    def _footer(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D9E2EC"))
        canvas.line(0.65*inch, 0.55*inch, 7.85*inch, 0.55*inch)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#627D98"))
        canvas.drawString(0.68*inch, 0.37*inch, "MarketMind | Informational use only; not investment advice")
        canvas.drawRightString(7.82*inch, 0.37*inch, f"Page {doc.page}")
        canvas.restoreState()

    def generate_report(self):
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            output_path = os.path.join(self.output_dir, f"{self.company}_report.pdf")
            data = self._load_data()
            financial = data.get("financial", {})
            company = self._company_name(data)
            doc = SimpleDocTemplate(
                output_path, pagesize=letter,
                rightMargin=0.65*inch, leftMargin=0.65*inch,
                topMargin=0.55*inch, bottomMargin=0.72*inch,
                title=f"MarketMind Analysis - {company}",
                author="MarketMind",
            )
            story = self._header(company, financial)
            story.extend(self._overview(data, company))
            story.append(Spacer(1, 10))
            story.extend(self._news(data))
            story.append(Spacer(1, 8))
            story.extend(self._analysis(data))
            doc.build(story, onFirstPage=self._footer, onLaterPages=self._footer)
            print(f"Report generated successfully: {output_path}")
            return True
        except Exception as exc:
            print(f"Error generating report: {exc}")
            return False

    def run(self):
        return self.generate_report()


if __name__ == "__main__":
    ReportWriterAgent(company="Samsung").run()
