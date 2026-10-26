"""Command-line entry point for Capital Compass."""

from agents.company_research import CompanyResearchPipeline, choose_peer, select_company


def run_capital_compass(company: str, competitor: str | None = None):
    """Resolve a public company, optionally choose a peer, and create a brief."""
    primary = select_company(company)
    if not primary:
        return False
    if competitor:
        peer = select_company(competitor)
    else:
        peer = choose_peer(primary)
    try:
        CompanyResearchPipeline().run(primary, peer)
        return True
    except Exception as exc:
        print(f"Capital Compass could not complete this run: {exc}")
        return False


if __name__ == "__main__":
    print("\nCAPITAL COMPASS - Company Research, Made Clear")
    print("Enter a listed company name or its Yahoo Finance ticker.")
    print("Examples: Apple, Tesla, TCS.NS, 6758.T, 005930.KS")
    company_query = input("\nCompany: ").strip()
    if company_query:
        run_capital_compass(company_query)
    else:
        print("Enter a company name or ticker to continue.")
