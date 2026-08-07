import json
import os


class Memory:

    def __init__(self):

        self.file_path = os.path.join(
            "data",
            "memory.json"
        )

        os.makedirs("data", exist_ok=True)

        if not os.path.exists(self.file_path):

            with open(
                self.file_path,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump([], file, indent=4)

    def load(self):

        try:

            with open(
                self.file_path,
                "r",
                encoding="utf-8"
            ) as file:

                return json.load(file)

        except (FileNotFoundError, json.JSONDecodeError):

            return []

    def save(self, memories):

        with open(
            self.file_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                memories,
                file,
                indent=4,
                ensure_ascii=False
            )

    def add(self, memory):

        memory = memory.strip()

        if not memory:
            return False

        memories = self.load()

        # Don't save duplicates
        for existing in memories:

            if existing.lower() == memory.lower():
                return False

        memories.append(memory)

        self.save(memories)

        return True

    def remove(self, memory):

        memories = self.load()

        new_memories = [
            item for item in memories
            if item.lower() != memory.lower()
        ]

        if len(new_memories) == len(memories):
            return False

        self.save(new_memories)

        return True

    def get_all(self):

        return self.load()

    def search(self, query):

        memories = self.load()

        query_words = set(
            query.lower().split()
        )

        results = []

        for memory in memories:

            memory_words = set(
                memory.lower().split()
            )

            common_words = query_words & memory_words

            # At least one meaningful word matches
            meaningful_words = {
                word for word in common_words
                if len(word) > 2
            }

            if meaningful_words:

                results.append(memory)

        return results

    def clear(self):

        self.save([])

        return True