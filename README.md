# MarketMind

An AI-powered market research and analysis tool that helps gather and analyze company information from multiple sources.

## Features

- Research Agent: Scrapes news, press releases, and social media
- Financial Analyst Agent: Fetches stock data and financials
- Sentiment Analyst Agent: Analyzes public sentiment and legal risks

## Setup

1. Clone the repository:
```bash
git clone https://github.com/ManthanN75/marketMind.git
cd marketMind
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and add your API keys:
```bash
cp .env.example .env
```

5. Run the agents:
```bash
python agents/research_agent.py
python agents/financial_analyst_agent.py
python agents/sentiment_analyst_agent.py
```

## Configuration

Create a `.env` file with the following variables:
- `GEMINI_API_KEY`: Google Gemini API key
- `TWITTER_API_KEY`: Twitter/X API key
- `TWITTER_API_SECRET`: Twitter/X API secret

## Project Structure

```
MarketMind/
├── agents/
│   ├── research_agent.py
│   ├── financial_analyst_agent.py
│   └── sentiment_analyst_agent.py
├── data/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```
