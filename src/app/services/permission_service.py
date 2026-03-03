from src.app.models.user import User


class PermissionService:
    @staticmethod
    def get_full_geo_scope(user: User):
        """Returns all geographical tags associated with the user."""
        return {
            "territory_id": getattr(user, 'assigned_territory_id', None),
            "area_id": getattr(user, 'assigned_area_id', None),
            "region_id": getattr(user, 'assigned_region_id', None),
            "state_id": getattr(user, 'assigned_state_id', None),
            "zone_id": getattr(user, 'assigned_zone_id', None)
        }

    @staticmethod
    def apply_geo_filter(query, model, user: User):
        """
        Dynamically applies the most granular geographic filter possible.
        Prevents upward blindness and data leaks.
        """
        scope = PermissionService.get_full_geo_scope(user)

        # We check from smallest (Territory) to largest (Zone)
        geo_columns = ["territory_id", "area_id", "region_id", "state_id", "zone_id"]

        for geo_col in geo_columns:
            # If the database table has this column, AND the user has this ID assigned
            if hasattr(model, geo_col) and scope.get(geo_col) is not None:
                return query.filter(getattr(model, geo_col) == scope[geo_col])

        # FAIL CLOSED: If the user has no matching geography for this table,
        # force an impossible condition so they see nothing (Data Leak Prevention)
        # Note: Admins bypass this entirely at the router level.
        return query.filter(model.id == -1)

    @staticmethod
    def get_geo_scope(user: User):
        """Legacy fallback for endpoints doing manual dict unpacking (**scope)"""
        scope = PermissionService.get_full_geo_scope(user)
        # Return only the keys that have a value
        return {k: v for k, v in scope.items() if v is not None}