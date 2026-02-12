class PermissionService:
    @staticmethod
    def get_user_data_scope(user):
        """Returns a filter for SQL queries based on user role"""
        if user.role.name == "Admin":
            return {} # See everything
        elif user.role.name == "ZSM":
            return {"zone_id": user.assigned_zone_id}
        elif user.role.name == "RSM":
            return {"region_id": user.assigned_region_id}
        # ... and so on for SO/Territory