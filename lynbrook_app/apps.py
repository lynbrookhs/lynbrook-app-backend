from django.contrib.admin.apps import AdminConfig


class CoreAdminConfig(AdminConfig):
    default_site = "lynbrook_app.admin.CoreAdmin"
