from django.apps import AppConfig


class CompaniesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.companies'
    verbose_name = 'Companies'
    
    def ready(self):
        """Import signals when the app is ready"""
        try:
            import apps.companies.signals  # noqa F401
        except ImportError:
            pass
