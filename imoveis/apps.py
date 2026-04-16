from django.apps import AppConfig


class ImoveisConfig(AppConfig):
    name = 'imoveis'

    def ready(self):
        import imoveis.signals  # noqa: F401
