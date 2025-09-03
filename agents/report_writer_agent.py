from datetime import datetime
import json
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch

class ReportWriterAgent:
    def __init__(self, company, input_dir="data", output_dir="reports"):
        self.company = company
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=16
        ))
        self.styles.add(ParagraphStyle(
            name='SubHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=12
        ))

    def _load_data(self):
        """Load data from all agent outputs."""
        data = {}
        files = {
            'research': 'raw_data.json',
            'financial': 'financial_data.json',
            'sentiment': 'sentiment_data.json',
            'analysis': 'analysis_data.json'
        }
        
        for key, filename in files.items():
            try:
                with open(os.path.join(self.input_dir, filename), 'r') as f:
                    data[key] = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load {filename}: {str(e)}")
                data[key] = {}
                
        return data

    def _create_header(self):
        """Create report header elements."""
        elements = []
        elements.append(Paragraph(
            f"Market Analysis Report: {self.company}",
            self.styles['Title']
        ))
        elements.append(Paragraph(
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, 0.5*inch))
        return elements

    def _create_news_section(self, data):
        """Create news section."""
        elements = []
        elements.append(Paragraph("Recent News", self.styles['SectionHeader']))
        
        if news := data.get('research', {}).get('news', []):
            for article in news[:5]:  # Show top 5 news
                elements.append(Paragraph(
                    f"• {article.get('title', 'No title')}",
                    self.styles['Normal']
                ))
                elements.append(Spacer(1, 0.1*inch))
        else:
            elements.append(Paragraph("No recent news available", self.styles['Normal']))
            
        elements.append(Spacer(1, 0.3*inch))
        return elements

    def _create_financial_section(self, data):
        """Create financial analysis section."""
        elements = []
        elements.append(Paragraph("Financial Analysis", self.styles['SectionHeader']))
        
        financial_data = data.get('financial', {})
        if financial_data:
            # Create financial metrics table
            metrics = [
                ['Metric', 'Value'],
                ['Current Price', f"${financial_data.get('current_price', 'N/A')}"],
                ['Price Change', f"{financial_data.get('price_change_percent', 'N/A')}%"],
                ['Market Cap', f"${financial_data.get('market_cap', 'N/A'):,}"],
            ]
            
            table = Table(metrics, colWidths=[2*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("No financial data available", self.styles['Normal']))
            
        elements.append(Spacer(1, 0.3*inch))
        return elements

    def _create_sentiment_section(self, data):
        """Create sentiment analysis section."""
        elements = []
        elements.append(Paragraph("Market Sentiment", self.styles['SectionHeader']))
        
        sentiment_data = data.get('sentiment', {}).get('sentiment_analysis', {})
        if sentiment_data:
            elements.append(Paragraph(
                f"Overall Sentiment Score: {sentiment_data.get('overall_score', 'N/A')}",
                self.styles['Normal']
            ))
            
            if legal_concerns := data.get('sentiment', {}).get('legal_concerns', []):
                elements.append(Paragraph("Legal Concerns:", self.styles['SubHeader']))
                for concern in legal_concerns:
                    elements.append(Paragraph(
                        f"• {concern.get('description', 'N/A')}",
                        self.styles['Normal']
                    ))
        else:
            elements.append(Paragraph("No sentiment data available", self.styles['Normal']))
            
        elements.append(Spacer(1, 0.3*inch))
        return elements

    def _create_analysis_section(self, data):
        """Create market analysis section."""
        elements = []
        elements.append(Paragraph("Market Analysis", self.styles['SectionHeader']))
        
        analysis_data = data.get('analysis', {})
        if analysis_data:
            # Market Trends
            if trends := analysis_data.get('market_trends', []):
                elements.append(Paragraph("Key Trends:", self.styles['SubHeader']))
                for trend in trends:
                    elements.append(Paragraph(
                        f"• {trend.get('description', 'N/A')}",
                        self.styles['Normal']
                    ))
                    
            # Opportunities
            if opportunities := analysis_data.get('opportunities', []):
                elements.append(Paragraph("Opportunities:", self.styles['SubHeader']))
                for opp in opportunities:
                    elements.append(Paragraph(
                        f"• {opp.get('description', 'N/A')}",
                        self.styles['Normal']
                    ))
        else:
            elements.append(Paragraph("No market analysis available", self.styles['Normal']))
            
        return elements

    def generate_report(self):
        """Generate the complete PDF report."""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Setup PDF document
            output_path = os.path.join(self.output_dir, f"{self.company}_report.pdf")
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Load all data
            data = self._load_data()
            
            # Build report elements
            elements = []
            elements.extend(self._create_header())
            elements.extend(self._create_news_section(data))
            elements.extend(self._create_financial_section(data))
            elements.extend(self._create_sentiment_section(data))
            elements.extend(self._create_analysis_section(data))
            
            # Generate PDF
            doc.build(elements)
            print(f"Report generated successfully: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error generating report: {str(e)}")
            return False

    def run(self):
        """Execute the agent's tasks."""
        return self.generate_report()

if __name__ == "__main__":
    agent = ReportWriterAgent(company="Samsung")
    agent.run()