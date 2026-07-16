import yfinance as yf
from langchain_core.tools import tool

@tool
def get_stock_price(ticker: str) -> str:
    """
    Get the current stock price and key metrics for a given ticker symbol.
    Use this when the user asks about stock prices, market cap, PE ratio, or company info.
    Example tickers: AAPL, TSLA, RELIANCE.NS, TCS.NS
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        price = info.get("currentPrice") or info.get("regularMarketPrice", "N/A")
        currency = info.get("currency", "USD")
        name = info.get("longName", ticker)
        market_cap = info.get("marketCap", "N/A")
        pe_ratio = info.get("trailingPE", "N/A")
        week_high = info.get("fiftyTwoWeekHigh", "N/A")
        week_low = info.get("fiftyTwoWeekLow", "N/A")
        sector = info.get("sector", "N/A")

        if market_cap != "N/A":
            market_cap = f"{market_cap:,.0f}"

        return (
            f"**{name} ({ticker.upper()})**\n"
            f"- Current Price: {price} {currency}\n"
            f"- Market Cap: {market_cap} {currency}\n"
            f"- P/E Ratio: {pe_ratio}\n"
            f"- 52-Week High: {week_high}\n"
            f"- 52-Week Low: {week_low}\n"
            f"- Sector: {sector}"
        )
    except Exception as e:
        return f"Error fetching stock data for {ticker}: {str(e)}"


@tool
def get_stock_history(ticker: str, period: str = "1mo") -> str:
    """
    Get historical stock price data for a given ticker symbol.
    Period options: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y
    Use when the user asks about stock performance over time.
    """
    try:
        stock = yf.Ticker(ticker.upper())
        hist = stock.history(period=period)

        if hist.empty:
            return f"No historical data found for {ticker}."

        start_price = round(hist["Close"].iloc[0], 2)
        end_price = round(hist["Close"].iloc[-1], 2)
        change_pct = round(((end_price - start_price) / start_price) * 100, 2)
        high = round(hist["High"].max(), 2)
        low = round(hist["Low"].min(), 2)
        avg_vol = round(hist["Volume"].mean(), 0)

        direction = "📈" if change_pct >= 0 else "📉"

        return (
            f"**{ticker.upper()} — {period} Performance** {direction}\n"
            f"- Start Price: {start_price}\n"
            f"- End Price: {end_price}\n"
            f"- Change: {change_pct}%\n"
            f"- Period High: {high}\n"
            f"- Period Low: {low}\n"
            f"- Avg Daily Volume: {avg_vol:,.0f}"
        )
    except Exception as e:
        return f"Error fetching history for {ticker}: {str(e)}"
