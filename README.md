# MarketMind

AI-powered market research and analysis tool that gathers and analyzes company information from multiple sources globally.

## Features

- Research Agent: Global news and press release scraping
- Financial Analyst: Real-time stock data and financial metrics
- Sentiment Analyst: News sentiment and legal risk detection
- Data Analyst: Market trends and competitor analysis
- Regulatory Analyst: Global compliance monitoring
- Report Writer: Comprehensive PDF report generation

## Setup

1. Clone the repository:
```bash
git clone https://github.com/ManthanN75/marketMind.git
cd marketMind
```

2. Create virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. Run the analysis:
```bash
python main.py
```

## Usage

Enter any publicly traded company name when prompted. Examples:
- US: Apple, Tesla, Microsoft
- India: Maruti Suzuki, ITC, Vedanta
- Global: BMW, Toyota, Samsung

## Output

- JSON files in `data/` directory
- PDF report in `reports/` directory
