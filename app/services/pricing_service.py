from sqlalchemy.orm import Session
from src.app.models.pricing import TradeScheme
from decimal import Decimal

class PricingService:
    @staticmethod
    def calculate_item_pricing(db: Session, product_id: int, base_price: Decimal, dispatch_qty: int):
        """
        Evaluates active trade schemes for a product.
        Returns: (final_price_per_case, free_qty_awarded)
        """
        # Fetch the active scheme (Simplification: assuming 1 active scheme per product)
        scheme = db.query(TradeScheme).filter(
            TradeScheme.product_id == product_id,
            TradeScheme.is_active == True
        ).first()

        final_price = base_price
        free_qty = 0

        # If a scheme exists and the customer bought enough to trigger it...
        if scheme and dispatch_qty >= scheme.min_qty:
            # 1. Apply Discount
            if scheme.discount_percent > 0:
                discount_amount = base_price * (Decimal(scheme.discount_percent) / 100)
                final_price = base_price - discount_amount

            # 2. Apply Free Goods (e.g., "Buy 10 get 2 free". If they buy 25, they get 4 free)
            if scheme.free_qty > 0:
                multiplier = dispatch_qty // scheme.min_qty
                free_qty = multiplier * scheme.free_qty

        return final_price, free_qty