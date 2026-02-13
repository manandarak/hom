# src/app/services/permission_service.py
class PermissionService:
    @staticmethod
    def get_user_data_scope(user):
        """Returns a SQLAlchemy filter dictionary based on user hierarchy"""
        if user.role.name == "Admin":
            return {}  # Full access

        elif user.role.name == "ZSM":
            return {"zone_id": user.assigned_zone_id}

        elif user.role.name == "RSM":
            return {"region_id": user.assigned_region_id}

        elif user.role.name == "SO":
            return {"territory_id": user.assigned_territory_id}

        return {"id": -1}  # Default to no access if role is unrecognized