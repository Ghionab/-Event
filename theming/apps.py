from django.apps import AppConfig


class ThemingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'theming'
    verbose_name = 'Dynamic Event Theming'
    
    def ready(self):
        """Initialize app when Django starts"""
        # Import signals if we add them later
        pass
