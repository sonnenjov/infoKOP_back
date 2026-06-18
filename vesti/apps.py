from django.apps import AppConfig

class VestiConfig(AppConfig):
    name = 'vesti'

    def ready(self):
        import vesti.signals