class BaseController:
    def __init__(self, application):
        self.application = application


    def register_handlers(self):
        """Має бути перевизначений у дочірньому класі."""
        raise NotImplementedError
