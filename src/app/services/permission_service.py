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

        elif role == "ZSM" or role == "SuperStockist":
            if not user.assigned_zone_id:
                return {"id": -1}
            return {"zone_id": user.assigned_zone_id}

        elif role == "RSM":
            if not user.assigned_region_id:
                return {"id": -1}
            return {"region_id": user.assigned_region_id}

        elif role == "ASM":
            if not user.assigned_area_id:
                return {"id": -1}
            return {"area_id": user.assigned_area_id}

        elif role == "SO" or role == "Retailer":
            if not user.assigned_territory_id:
                return {"id": -1}
            return {"territory_id": user.assigned_territory_id}

        elif role == "Distributor":
            if not user.assigned_state_id:
                return {"id": -1}
            return {"state_id": user.assigned_state_id}

        return {"id": -1}