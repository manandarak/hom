# src/app/services/permission_service.py

class PermissionService:
    @staticmethod
    def get_geo_scope(user):
        """
        Returns a dictionary for filtering queries based on geographic scoping.
        Make sure your target models (e.g., Order, Finance) have these corresponding columns
        or are joined with the Geography tables during the query.
        """
        if not user.role:
            return {"id": -1}

        role = user.role.name
        if role == "Admin":
            return {}

        elif role == "ZSM":
            return {"zone_id": user.assigned_zone_id}
        elif role == "RSM":
            return {"region_id": user.assigned_region_id}
        elif role == "ASM":
            return {"area_id": user.assigned_area_id}
        elif role == "SO":
            return {"territory_id": user.assigned_territory_id}

        elif role == "SuperStockist":
            return {"zone_id": user.assigned_zone_id}

        elif role == "Distributor":
            return {"state_id": user.assigned_state_id}

        elif role == "Retailer":
            return {"territory_id": user.assigned_territory_id}
        return {"id": -1}