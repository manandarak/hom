class PermissionService:
    @staticmethod
    def get_user_data_scope(user):
        """Returns a SQLAlchemy filter dict based on the User's geography columns"""
        if user.role.name == "Admin":
            return {}  # Empty dict means NO filter (Full access)

        elif user.role.name == "ZSM":
            return {"assigned_zone_id": user.assigned_zone_id}

        elif user.role.name == "RSM":
            return {"assigned_region_id": user.assigned_region_id}

        elif user.role.name == "ASM":
            return {"assigned_area_id": user.assigned_area_id}

        elif user.role.name == "SO":
            return {"assigned_territory_id": user.assigned_territory_id}

        return {"id": -1}  # Failsafe: return impossible ID if role unknown