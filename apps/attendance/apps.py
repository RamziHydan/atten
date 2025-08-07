from django.apps import AppConfig


class AttendanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.attendance'
    verbose_name = 'Attendance'
    
    def ready(self):
        """Import signals when the app is ready"""
        try:
            import apps.attendance.signals  # noqa F401
        except ImportError:
            pass
