from pydantic import BaseModel, Field


class Settings(BaseModel):
    # TODO remove these temporary values
    ssl_keyfile: str = "/Users/david/code/iris/key.pem"
    ssl_certfile: str = "/Users/david/code/iris/cert.pem"
    data_path: str = "/Users/david/code/iris/web_messages/"
    base_language: str = "en"
    supported_languages: list[str] = [
        "ru",
        "es",
    ]
    static_root: str = "/Users/david/code/iris/my-app/build"

    @classmethod
    def load(cls):
        """
        Loop through env vars that match the settings
        """
        pass


settings = Settings()
