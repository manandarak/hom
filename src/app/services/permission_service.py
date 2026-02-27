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
            return {"id": -1}  # Failsafe if user has no role

        role = user.role.name

        # 1. Admin - Full Access
        if role == "Admin":
            return {}

        # 2. Internal Team Hierarchy
        elif role == "ZSM":
            return {"zone_id": user.assigned_zone_id}
        elif role == "RSM":
            return {"region_id": user.assigned_region_id}
        elif role == "ASM":
            return {"area_id": user.assigned_area_id}
        elif role == "SO":
            return {"territory_id": user.assigned_territory_id}

        # 3. Partners - Geographic Scoping
        elif role == "SuperStockist":
            # SS mapped to Zone
            return {"zone_id": user.assigned_zone_id}

        elif role == "Distributor":
            # Distributor mapped to State (Assuming Region = State in your DB schema)
            return {"region_id": user.assigned_region_id}

        elif role == "Retailer":
            # Retailer mapped to Territory
            return {"territory_id": user.assigned_territory_id}

        # Failsafe for unknown roles
        return {"id": -1}