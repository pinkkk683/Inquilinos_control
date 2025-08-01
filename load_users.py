import os, json

class LoadUsers:
    def load(self, file) -> json:
            if not os.path.exists(file):
                return {}
            with open(file, 'r') as f:
                return json.load(f)