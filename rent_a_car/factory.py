class EndpointMixinFactory:
    """Return an Endpoint class, built using the
    class keyword"""

    @staticmethod
    def create_endpoint(blueprint):
        class Endpoint:
            blp = blueprint

            @classmethod
            def endpoint(self):
                return f"{self.blp.name}.{self.__name__}"

            def __str__(self):
                return f"{self.blp.name}.{type(self).__name__}"

        return Endpoint
