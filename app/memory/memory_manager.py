import json
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

MAX_MEMORY_ENTRIES = 1000

class MemoryManager:
    def __init__(self):
        self.long_term_file = "app/memory/long_term.json"
        self.short_term_file = "app/memory/short_term.json"
        self.traits_file = "app/memory/traits.json"
        self.user_profile_file = "app/memory/user_profile.json"
        # Ensure files exist
        for file in [self.long_term_file, self.short_term_file, self.traits_file, self.user_profile_file]:
            try:
                if not os.path.exists(file):
                    os.makedirs(os.path.dirname(file), exist_ok=True)
                    with open(file, 'w') as f:
                        json.dump({}, f)
            except OSError as e:
                logger.warning(f"Could not create memory file {file}: {e}")

    def retrieve_context(self, input_data):
        try:
            with open(self.short_term_file, 'r') as f:
                short_term = json.load(f)
            return short_term
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not read short-term memory: {e}")
            return {}

    def _atomic_write(self, filepath, data):
        """Write data to file atomically using temp file + rename."""
        dir_name = os.path.dirname(filepath)
        try:
            fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
            with os.fdopen(fd, 'w') as f:
                json.dump(data, f)
            os.replace(tmp_path, filepath)
        except OSError as e:
            logger.error(f"Atomic write failed for {filepath}: {e}")
            # Clean up temp file on failure
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def update(self, query, result):
        try:
            with open(self.short_term_file, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = {}

        data[str(query)] = result

        # Enforce size limit to prevent unbounded growth
        if len(data) > MAX_MEMORY_ENTRIES:
            keys = list(data.keys())
            for key in keys[:len(keys) - MAX_MEMORY_ENTRIES]:
                del data[key]

        self._atomic_write(self.short_term_file, data)