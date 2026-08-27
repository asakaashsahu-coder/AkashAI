import json
import os
import re
from difflib import SequenceMatcher


class Memory:

    def __init__(self):
        project_root = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        self.file_path = os.path.join(
            project_root,
            "data",
            "memory.json"
        )

        os.makedirs(
            os.path.dirname(self.file_path),
            exist_ok=True
        )

        if not os.path.exists(self.file_path):
            self.save([])

    # --------------------------------------------------
    # NORMALIZE TEXT
    # --------------------------------------------------

    def _normalize(self, text):
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9+#.\s]", " ", text)
        return " ".join(text.split())

    def _keywords(self, text):
        stop_words = {
            "a", "an", "the", "and", "or", "but", "is", "am",
            "are", "was", "were", "be", "been", "being", "to",
            "of", "in", "on", "at", "for", "from", "with", "that",
            "this", "it", "my", "me", "i", "im", "i'm", "do",
            "does", "did", "what", "who", "where", "when", "why",
            "how", "you", "your", "about", "remember", "know"
        }

        words = self._normalize(text).split()

        return {
            word for word in words
            if len(word) > 2 and word not in stop_words
        }

    # --------------------------------------------------
    # LOAD / SAVE
    # --------------------------------------------------

    def load(self):
        try:
            with open(
                self.file_path,
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

            # Backward compatible with the old memory.json
            # format, which is simply a list of strings.
            if not isinstance(data, list):
                return []

            return [
                str(item).strip()
                for item in data
                if str(item).strip()
            ]

        except (
            FileNotFoundError,
            json.JSONDecodeError,
            OSError
        ):
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

    # --------------------------------------------------
    # ADD / REMOVE
    # --------------------------------------------------

    def add(self, memory):
        memory = " ".join(memory.strip().split())

        if not memory:
            return False

        memories = self.load()
        normalized_new = self._normalize(memory)

        for existing in memories:
            if self._normalize(existing) == normalized_new:
                return False

        memories.append(memory)
        self.save(memories)
        return True

    def remove(self, memory):
        memories = self.load()
        normalized_target = self._normalize(memory)

        new_memories = [
            item for item in memories
            if self._normalize(item) != normalized_target
        ]

        if len(new_memories) == len(memories):
            return False

        self.save(new_memories)
        return True

    def remove_best_match(self, text):
        matches = self.search(text, limit=3)

        if not matches:
            return None

        target = self._normalize(text)

        # Prefer an exact match if one exists.
        for memory in matches:
            if self._normalize(memory) == target:
                self.remove(memory)
                return memory

        # Only auto-delete when there is one clear match.
        if len(matches) == 1:
            self.remove(matches[0])
            return matches[0]

        return matches

    # --------------------------------------------------
    # READ / SEARCH
    # --------------------------------------------------

    def get_all(self):
        return self.load()

    def search(self, query, limit=6):
        memories = self.load()

        if not memories:
            return []

        query_normalized = self._normalize(query)
        query_words = self._keywords(query)
        scored = []

        for index, memory in enumerate(memories):
            memory_normalized = self._normalize(memory)
            memory_words = self._keywords(memory)

            common_words = query_words & memory_words
            score = len(common_words) * 3

            if query_normalized and query_normalized in memory_normalized:
                score += 8

            if memory_normalized and memory_normalized in query_normalized:
                score += 8

            similarity = SequenceMatcher(
                None,
                query_normalized,
                memory_normalized
            ).ratio()

            score += similarity

            if common_words or similarity >= 0.42:
                scored.append((score, index, memory))

        scored.sort(
            key=lambda item: (item[0], item[1]),
            reverse=True
        )

        return [
            item[2]
            for item in scored[:limit]
        ]

    def context_for(self, query, limit=8):
        memories = self.load()

        if not memories:
            return []

        # When only a few facts are stored, including all of them gives
        # Jeroo reliable personal context without adding much prompt size.
        if len(memories) <= limit:
            return memories

        matches = self.search(
            query,
            limit=limit
        )

        if matches:
            return matches

        # If no strong keyword match exists, use the most recently saved
        # facts as a small fallback context.
        return memories[-min(4, limit):]

    # --------------------------------------------------
    # CLEAR
    # --------------------------------------------------

    def clear(self):
        self.save([])
        return True
