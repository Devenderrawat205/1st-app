from django.core.management.base import BaseCommand, CommandError
from Researchers.models import Stock  # Assuming 'Researchers' is the app name in apps.py
import yfinance as yf


class Command(BaseCommand):
    help = 'Populates the database with a sample list of financial symbols.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing symbols before populating.',
        )
        parser.add_argument(
            '--fetch-names',
            action='store_true',
            help='Attempt to fetch official names from yfinance for symbols (slower).',
        )

    def handle(self, *args, **kwargs):
        clear_existing = kwargs['clear']
        fetch_names_flag = kwargs['fetch_names']

        if clear_existing:
            self.stdout.write(self.style.WARNING('Deleting all existing symbols...'))
            deleted_count, _ = Stock.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} symbols.'))

        self.stdout.write("Populating symbols...")

        # Structure: (yahoo_symbol, default_display_name, category_constant_from_Stock_model)
        symbols_to_populate = [
            # --- 1. Indexes ---
            ('^GSPC', 'S&P 500', Stock.CATEGORY_INDEX),
            ('^IXIC', 'NASDAQ Composite', Stock.CATEGORY_INDEX),
            ('^DJI', 'Dow Jones Industrial Average', Stock.CATEGORY_INDEX),
            ('^FTSE', 'FTSE 100 (UK)', Stock.CATEGORY_INDEX),
            ('^N225', 'Nikkei 225 (Japan)', Stock.CATEGORY_INDEX),
            ('IMOEX.ME', 'MOEX Russia Index', Stock.CATEGORY_INDEX),
            ('^BSESN', 'BSE SENSEX (India)', Stock.CATEGORY_INDEX),
            ('SPY', 'SPDR S&P 500 ETF Trust', Stock.CATEGORY_INDEX),  # Also an ETF

            # --- 2. Stocks ---
            ('AAPL', 'Apple Inc.', Stock.CATEGORY_STOCK),
            ('MSFT', 'Microsoft Corp.', Stock.CATEGORY_STOCK),
            ('GOOGL', 'Alphabet Inc. (Google Class C)', Stock.CATEGORY_STOCK),
            ('AMZN', 'Amazon.com, Inc.', Stock.CATEGORY_STOCK),
            ('TSLA', 'Tesla, Inc.', Stock.CATEGORY_STOCK),
            ('NVDA', 'NVIDIA Corporation', Stock.CATEGORY_STOCK),
            ('JPM', 'JPMorgan Chase & Co.', Stock.CATEGORY_STOCK),
            ('V', 'Visa Inc.', Stock.CATEGORY_STOCK),
            ('RELIANCE.NS', 'Reliance Industries Limited (India)', Stock.CATEGORY_STOCK),
            ('BABA', 'Alibaba Group Holding Limited', Stock.CATEGORY_STOCK),

            # --- 3. Currency Pairs (Forex from Yahoo Finance format) ---
            ('EURUSD=X', 'EUR to USD', Stock.CATEGORY_CURRENCY),
            ('GBPUSD=X', 'GBP to USD', Stock.CATEGORY_CURRENCY),
            ('USDJPY=X', 'USD to JPY', Stock.CATEGORY_CURRENCY),
            ('USDCAD=X', 'USD to CAD', Stock.CATEGORY_CURRENCY),
            ('AUDUSD=X', 'AUD to USD', Stock.CATEGORY_CURRENCY),
            ('EURGBP=X', 'EUR to GBP', Stock.CATEGORY_CURRENCY),
            ('INR=X', 'USD to INR', Stock.CATEGORY_CURRENCY),

            # --- 4. Commodities (Futures tickers from Yahoo Finance or common ETFs) ---
            ('CL=F', 'Crude Oil WTI Futures', Stock.CATEGORY_COMMODITY),
            ('GC=F', 'Gold Futures', Stock.CATEGORY_COMMODITY),
            ('SI=F', 'Silver Futures', Stock.CATEGORY_COMMODITY),
            ('HG=F', 'Copper Futures', Stock.CATEGORY_COMMODITY),
            ('ZS=F', 'Soybean Futures', Stock.CATEGORY_COMMODITY),
            ('NG=F', 'Natural Gas Futures', Stock.CATEGORY_COMMODITY),
            ('GLD', 'SPDR Gold Shares ETF', Stock.CATEGORY_COMMODITY),
            ('SLV', 'iShares Silver Trust ETF', Stock.CATEGORY_COMMODITY),
        ]

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for ticker_symbol, default_name, category in symbols_to_populate:
            current_name = default_name

            if fetch_names_flag:
                self.stdout.write(f"Attempting to fetch name for {ticker_symbol}...")
                try:
                    # Ensure yfinance Ticker object is created correctly
                    ticker_obj = yf.Ticker(ticker_symbol)
                    ticker_info = ticker_obj.info if hasattr(ticker_obj,
                                                             'info') else {}  # Handle cases where info might be missing

                    name_priority = ['longName', 'shortName', 'displayName', 'description']
                    fetched_name = None
                    for name_key in name_priority:
                        if ticker_info and name_key in ticker_info and ticker_info[name_key]:
                            fetched_name = ticker_info[name_key]
                            break

                    if fetched_name:
                        current_name = fetched_name
                        self.stdout.write(self.style.SUCCESS(f"  Fetched name: {current_name}"))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"  Could not fetch specific name for {ticker_symbol} (info: {ticker_info is not None}), using default: '{default_name}'"))
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  Error fetching info for {ticker_symbol}: {e}. Using default name."))

            try:
                stock_obj, created = Stock.objects.get_or_create(
                    symbol=ticker_symbol,
                    defaults={'name': current_name, 'category': category}
                )

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"Created: {stock_obj.symbol} - {stock_obj.name} ({stock_obj.get_category_display()})"))
                else:
                    needs_update = False
                    if stock_obj.name != current_name:
                        stock_obj.name = current_name
                        needs_update = True
                    if stock_obj.category != category:
                        stock_obj.category = category
                        needs_update = True

                    if needs_update:
                        stock_obj.save()
                        updated_count += 1
                        self.stdout.write(self.style.NOTICE(
                            f"Updated: {stock_obj.symbol} - {stock_obj.name} ({stock_obj.get_category_display()})"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing symbol {ticker_symbol} for database: {e}"))
                skipped_count += 1
                continue

        self.stdout.write(self.style.SUCCESS(
            f"Symbol population complete. {created_count} created, {updated_count} updated, {skipped_count} skipped."
        ))