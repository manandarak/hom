from sqlalchemy.orm import Session
from src.app.models.geography import Territory, Area, Region

class TaxService:
    @staticmethod
    def get_retailer_state_id(db: Session, territory_id: int) -> int:
        """Traverses the geographic hierarchy to find the State ID of a Retailer's Territory."""
        state_id = db.query(Region.state_id) \
            .join(Area, Area.region_id == Region.id) \
            .join(Territory, Territory.area_id == Area.id) \
            .filter(Territory.id == territory_id) \
            .scalar()

        return state_id

    @staticmethod
    def calculate_gst(base_amount: float, gst_percent: float, seller_state_id: int, buyer_state_id: int):
        """Calculates CGST/SGST vs IGST based on location."""
        total_tax_amount = base_amount * (gst_percent / 100)

        tax_breakdown = {
            "base_amount": base_amount,
            "cgst": 0.0,
            "sgst": 0.0,
            "igst": 0.0,
            "total_tax": total_tax_amount,
            "final_amount": base_amount + total_tax_amount
        }

        # If both parties are in the same state: Split tax 50/50
        if seller_state_id == buyer_state_id:
            tax_breakdown["cgst"] = total_tax_amount / 2
            tax_breakdown["sgst"] = total_tax_amount / 2
        # If they are in different states: Full IGST
        else:
            tax_breakdown["igst"] = total_tax_amount

        return tax_breakdown