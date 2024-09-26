from iris.server.models import User, Role
import os

if __name__ == "__main__":
    uname = os.environ.get("IRIS_ADMIN_NAME", "admin")
    pw = os.environ.get("IRIS_ADMIN_PASSWORD", "admin")
    lang = os.environ.get("IRIS_ADMIN_LANG", "en")

    User(name=uname, password=pw, language=lang, role=Role.ADMIN).save_to_file()
