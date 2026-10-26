# Capital Compass

**Company research, made clear.** Capital Compass creates a source-linked brief for a public company and, when selected, a competitor. It combines financial performance, valuation context, recent company news, event headlines to review, and a plain-language business profile.

## What it does

- Finds listed-company candidates by name using Yahoo Finance search, or accepts a ticker directly. It asks you to confirm a match before using it.
- Suggests a competitor for selected common companies and lets you enter a different public company or skip the comparison. Suggestions are starting points; companies can differ in business mix.
- Compares share price returns over 1 month, 3 months, 6 months, 1 year, 3 years, and 5 years, plus available revenue/earnings growth, profit margin, return on equity, market capitalization, and valuation ratios.
- Calculates annualized volatility and maximum drawdown from daily adjusted prices, and compares returns with a listing-region benchmark.
- Retrieves recent Google News headlines, shows publisher/date/source links, and calculates a simple headline-tone estimate.
- Surfaces headlines that match legal, regulatory, safety, privacy, or controversy keywords for human review.
- Shows the provider's company profile and available annual R&D and capital-expenditure figures.
- Saves a timestamped JSON evidence snapshot and generates a readable PDF report.

## Run it

Python 3.11 or newer is recommended.

```powershell
# Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install -r requirements.txt

# Start the app
python main.py
```

Enter a company name or ticker. Confirm the matched listing, then accept the suggested competitor, enter another competitor, or type `skip`.

Examples: `Apple`, `Tesla`, `TCS.NS`, `6758.T`, `005930.KS`.

The core Capital Compass workflow does **not** require a Gemini API key. It uses Yahoo Finance data and Google News RSS, so it can run without Gemini availability or billing configuration.

## Output

Each run gets a unique directory, so reports cannot accidentally mix company data from an earlier run:

```text
data/runs/<ticker>_<run-id>/capital_compass_report.json
reports/<ticker>_<run-id>_capital_compass.pdf
```

The JSON file contains the figures, news items, event flags, source URLs, retrieval timestamps, and methodology used for the report. Reports are intended for reading and sharing; generated run files are excluded from Git.

## Data and interpretation

- Market and financial information comes from Yahoo Finance through `yfinance`; availability and completeness vary by listing and company.
- News is retrieved from Google News RSS for the past three months. An empty feed does not mean that no news or events exist.
- Headline tone is estimated with TextBlob from headline text and the RSS description. It is not polling of public opinion, full-article analysis, or a prediction.
- Event flags are keyword matches, not confirmation of wrongdoing. Open the linked article and verify its facts, legal status, date, and the company's response.
- R&D and capital expenditure are broad reported figures. R&D is not always technology-only, and capital expenditure includes investment across the business.
- Cross-market returns are percentages; currencies and market calendars differ. Valuation ratios need industry context.
- This project is for research and education. It does not provide investment advice or trading recommendations.

## Suggested competitor coverage

The app includes initial suggestions for pairs such as Apple/Samsung, Tesla/BYD, NVIDIA/AMD, Microsoft/Alphabet, Toyota/Volkswagen, and TCS/Infosys. For other companies, it searches Yahoo Finance for same-industry candidates when industry data is available; otherwise, enter a peer manually. Search matches are suggestions, not proof of direct competition, so the app explains their basis and keeps the user in control.

## Project structure

```text
main.py                          CLI entry point
agents/company_research.py       Company lookup, data collection, calculations, evidence
agents/capital_compass_report.py  Source-linked PDF report generation
```
