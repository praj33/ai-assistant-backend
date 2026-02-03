import json
import os

class MemoryManager:
    def __init__(self):
        self.long_term_file = "app/memory/long_term.json"
        self.short_term_file = "app/memory/short_term.json"
        self.traits_file = "app/memory/traits.json"
        self.user_profile_file = "app/memory/user_profile.json"
        # Ensure files exist
        for file in [self.long_term_file, self.short_term_file, self.traits_file, self.user_profile_file]:
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    json.dump({}, f)

    def retrieve_context(self, input_data):
        # Use embeddings + vector DB - simulate
        with open(self.short_term_file, 'r') as f:
            short_term = json.load(f)
        return short_term

    def update(self, query, result):
        # Store conversations + preferences
        with open(self.short_term_file, 'r') as f:
            data = json.load(f)
        data[str(query)] = result
        with open(self.short_term_file, 'w') as f:
            json.dump(data, f)