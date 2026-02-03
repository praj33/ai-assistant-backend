"""
SummaryFlow Module - Seeya's NLU Summary Engine
Provides stable, structured summaries with entity extraction and key points.
"""

import re
from typing import Dict, List, Any
from datetime import datetime

class SummaryFlow:
    def __init__(self):
        # Initialize NLP components
        self.entity_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'url': r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            'time': r'\b\d{1,2}:\d{2}(?:\s?[APMapm]{2})?\b'
        }

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text using regex patterns."""
        entities = {}
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                entities[entity_type] = list(set(matches))  # Remove duplicates
        return entities

    def extract_key_points(self, text: str) -> List[str]:
        """Extract key points from text using simple heuristics."""
        sentences = re.split(r'[.!?]+', text)
        key_points = []

        # Simple heuristics: sentences with keywords or longer sentences
        keywords = ['important', 'key', 'main', 'summary', 'conclusion', 'action', 'todo', 'deadline']

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Check for keywords
            if any(keyword in sentence.lower() for keyword in keywords):
                key_points.append(sentence)
            # Or if sentence is substantial length
            elif len(sentence.split()) > 10:
                key_points.append(sentence)

        return key_points[:5]  # Limit to 5 key points

    def generate_summary(self, text: str) -> Dict[str, Any]:
        """Generate a stable summary JSON schema."""
        entities = self.extract_entities(text)
        key_points = self.extract_key_points(text)

        # Simple extractive summary (first and last sentences + key points)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        summary_text = ""
        if sentences:
            summary_text = sentences[0]  # First sentence
            if len(sentences) > 1:
                summary_text += " " + sentences[-1]  # Last sentence

        return {
            "summary": summary_text,
            "key_points": key_points,
            "entities": entities,
            "word_count": len(text.split()),
            "sentence_count": len(sentences),
            "timestamp": datetime.now().isoformat(),
            "version": "summaryflow_v1"
        }

# Global instance
summary_flow = SummaryFlow()