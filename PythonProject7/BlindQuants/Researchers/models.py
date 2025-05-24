from django.db import models

class Stock(models.Model):
    """
    Represents a stock or other financial instrument with its symbol, name, and category.
    """
    CATEGORY_INDEX = 'IDX'
    CATEGORY_STOCK = 'STK'
    CATEGORY_CURRENCY = 'CRY'
    CATEGORY_COMMODITY = 'COM'
    # We won't list individual options due to their nature,
    # but you could have a category for 'StocksWithListedOptions' if needed for filtering.

    CATEGORY_CHOICES = [
        (CATEGORY_INDEX, 'Index'),
        (CATEGORY_STOCK, 'Stock'),
        (CATEGORY_CURRENCY, 'Currency Pair'),
        (CATEGORY_COMMODITY, 'Commodity'),
    ]

    symbol = models.CharField(max_length=20, unique=True) # Increased max_length for longer symbols
    name = models.CharField(max_length=255)
    category = models.CharField(
        max_length=3,
        choices=CATEGORY_CHOICES,
        default=CATEGORY_STOCK, # Default to stock if not specified
    )

    def __str__(self):
        return f"{self.symbol} ({self.get_category_display()})" # Show category in string representation