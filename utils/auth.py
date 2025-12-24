import json
import os

def check_login(username, password):
    users_file = os.path.join(os.path.dirname(__file__), "..", "users.json")
    if os.path.exists(users_file):
        with open(users_file, "r") as f:
            users = json.load(f)
        return users.get(username) == password
    return False
