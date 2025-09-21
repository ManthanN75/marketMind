# MarketMind 🧠📈

An intelligent multi-agent system for comprehensive market research and financial analysis. MarketMind leverages AI to gather, analyze, and synthesize company information from multiple global sources, providing actionable insights for investment decisions and market understanding.

## 🌟 Features

### Multi-Agent Architecture
- **Research Agent**: Scrapes news from Google News, Yahoo Finance, and MarketWatch
- **Financial Analyst**: Real-time stock data with global market support (NYSE, NASDAQ, NSE, KRX, TSE)
- **Sentiment Analyst**: AI-powered sentiment analysis with legal risk detection
- **Data Analyst**: Market trends, competitor analysis, and opportunity identification
- **Regulatory Analyst**: Compliance monitoring and regulatory risk assessment
- **Report Writer**: Professional PDF reports with comprehensive analysis

### Global Market Coverage
- **US Markets**: NYSE, NASDAQ (Apple, Tesla, Microsoft, McDonald's)
- **Indian Markets**: NSE, BSE (TCS, ITC, Vedanta, Reliance)
- **Asian Markets**: KRX, TSE (Samsung, Toyota, Sony, Honda)
- **European Markets**: XETRA (BMW, Mercedes, Volkswagen, SAP)

### Advanced Analytics
- Multi-currency support with regional formatting
- AI-powered news relevance scoring
- Legal risk detection and compliance monitoring
- Competitor analysis with industry categorization
- Automated report generation with professional formatting

## 🛠️ Technology Stack

- **AI/ML**: Google Gemini 1.5 Pro for advanced analysis
- **Data Sources**: Yahoo Finance, Google News, MarketWatch
- **Analysis**: TextBlob, NLTK for sentiment analysis
- **Visualization**: ReportLab for PDF generation
- **Data Processing**: Pandas, NumPy for financial calculations

## 📋 Prerequisites

- Python 3.8+
- Google Gemini API Key
- Internet connection for real-time data

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/ManthanN75/marketMind.git
cd marketMind

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your API keys
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Run Analysis
```bash
python main.py
```

## 💡 Usage Examples

### Supported Company Formats
```python
# US Companies
"Apple", "AAPL", "Tesla", "TSLA", "McDonald's", "MCD"

# Indian Companies  
"TCS", "TCS.NS", "ITC Limited", "Vedanta"

# Global Companies
"Samsung", "Toyota", "BMW.DE", "Sony"
```

### Sample Analysis Flow
1. **Enter Company Name**: `Tesla`
2. **Data Collection**: News scraping, financial data retrieval
3. **AI Analysis**: Sentiment analysis, risk assessment, trend identification
4. **Report Generation**: Comprehensive PDF with actionable insights

## 📊 Output Structure

```
marketMind/
├── data/
│   ├── raw_data.json          # Scraped news articles
│   ├── financial_data.json    # Stock data and metrics
│   ├── sentiment_data.json    # Sentiment analysis results
│   ├── analysis_data.json     # Market trends and insights
│   └── regulatory_data.json   # Compliance information
├── reports/
│   └── [Company]_report.pdf   # Professional analysis report
└── logs/
    └── analysis.log           # System logs
```

## 🔧 Configuration

### API Keys Required
- **Gemini API**: For advanced AI analysis and insights
- **Optional APIs**: Twitter/X API for social sentiment (future enhancement)

### Environment Variables
```bash
GEMINI_API_KEY=your_key_here
TWITTER_API_KEY=optional
TWITTER_API_SECRET=optional
```

## 🌍 Global Market Support

### Supported Exchanges
| Region | Exchange | Suffix | Example |
|--------|----------|--------|---------|
| USA | NYSE, NASDAQ | - | AAPL, TSLA |
| India | NSE | .NS | TCS.NS, ITC.NS |
| India | BSE | .BO | TCS.BO |
| South Korea | KRX | .KS | 005930.KS |
| Japan | TSE | .T | 7203.T |
| Germany | XETRA | .DE | BMW.DE |

### Currency Support
- USD ($) - US Dollar
- INR (₹) - Indian Rupee with Crore/Lakh formatting
- JPY (¥) - Japanese Yen
- KRW (₩) - Korean Won
- EUR (€) - Euro

## 🧮 Analysis Capabilities

### Financial Metrics
- Current price and price changes
- Market capitalization (multi-currency)
- P/E ratios and financial health indicators
- 52-week high/low ranges
- Trading volume analysis

### Sentiment Analysis
- News sentiment scoring (-1 to +1)
- Legal risk detection
- Market trend identification
- Social media sentiment (when configured)

### Competitive Intelligence
- Industry competitor mapping
- Market share analysis
- Competitive positioning
- Strategic opportunity identification

## 🐛 Troubleshooting

### Common Issues

**API Key Errors**
```bash
# Ensure your .env file contains:
GEMINI_API_KEY=your_actual_api_key
```

**Company Not Found**
- Try alternative company names or ticker symbols
- Check supported exchanges list
- Use full company names for better results

**Network Issues**
- Ensure stable internet connection
- Some regions may require VPN for certain data sources

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -m 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add comprehensive error handling
- Include unit tests for new features
- Update documentation for new capabilities

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini API for advanced AI capabilities
- Yahoo Finance for real-time financial data
- Various news sources for comprehensive coverage
- Open-source Python community for excellent libraries

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

---

**MarketMind** - Intelligent Market Analysis for Informed Decisions 🎯