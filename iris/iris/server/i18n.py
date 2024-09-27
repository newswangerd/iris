from collections import OrderedDict
import hashlib
import json
from functools import lru_cache

class I18NMessages:
    messages = [
        "Edit User",
        "QR Code",
        "Logout",
        "Delete",
        "Name",
        "Language",
        "English",
        "Russian",
        "Spanish",
        "Enable conversation mode?",
        "Username",
        "Password",
        "Login",
        "Add User",
        "Control Panel",
        "Understood",
        "Speak.",
        "Press and hold the red button.",
        "Release the button.",
        "Your message will be translated and sent to me.",
        "Instructions",
        "Your translated message.",
        "Interpreter"
    ]


    @classmethod
    @lru_cache
    def get_hash(cls):
        json_string = json.dumps(cls.messages)
        sha1_hash = hashlib.sha1()
        sha1_hash.update(json_string.encode('utf-8'))
        return sha1_hash.hexdigest()
