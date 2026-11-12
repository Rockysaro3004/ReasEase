"""
Extractive Summarization Service
Implements a frequency-based sentence scoring algorithm.
Pure Python implementation with no external model or NLTK corpus downloads required.
"""
import re
from collections import Counter

# Standard English stopwords list to filter non-informative words
STOPWORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren\'t',
    'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
    'can', 'can\'t', 'cannot', 'could', 'couldn\'t', 'did', 'didn\'t', 'do', 'does', 'doesn\'t', 'doing',
    'don\'t', 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', 'hadn\'t', 'has',
    'hasn\'t', 'have', 'haven\'t', 'having', 'he', 'he\'d', 'he\'ll', 'he\'s', 'her', 'here', 'here\'s',
    'hers', 'herself', 'him', 'himself', 'his', 'how', 'how\'s', 'i', 'i\'d', 'i\'ll', 'i\'m', 'i\'ve',
    'if', 'in', 'into', 'is', 'isn\'t', 'it', 'it\'s', 'its', 'itself', 'let\'s', 'me', 'more', 'most',
    'mustn\'t', 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other',
    'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', 'shan\'t', 'she', 'she\'d',
    'she\'ll', 'she\'s', 'should', 'shouldn\'t', 'so', 'some', 'such', 'than', 'that', 'that\'s', 'the',
    'their', 'theirs', 'them', 'themselves', 'then', 'there', 'there\'s', 'these', 'they', 'they\'d',
    'they\'ll', 'they\'re', 'they\'ve', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up',
    'very', 'was', 'wasn\'t', 'we', 'we\'d', 'we\'ll', 'we\'re', 'we\'ve', 'were', 'weren\'t', 'what',
    'what\'s', 'when', 'when\'s', 'where', 'where\'s', 'which', 'while', 'who', 'who\'s', 'whom',
    'why', 'why\'s', 'with', 'won\'t', 'would', 'wouldn\'t', 'you', 'you\'d', 'you\'ll', 'you\'re',
    'you\'ve', 'your', 'yours', 'yourself', 'yourselves', 'also', 'thus', 'therefore'
}


class ExtractiveSummarizer:
    """Frequency-based extractive summarizer for study materials."""

    @staticmethod
    def split_into_sentences(text):
        """Splits text into clean sentences using regex punctuation boundaries."""
        raw_sentences = re.split(r'(?<=[.!?])\s+', text)
        clean_sentences = []
        for s in raw_sentences:
            s_clean = s.strip().replace('\n', ' ')
            # Keep meaningful sentences with at least 4 words
            if len(s_clean.split()) >= 4:
                clean_sentences.append(s_clean)
        return clean_sentences

    @staticmethod
    def tokenize_words(text):
        """Extracts alphabetic lowercase words from text."""
        return re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

    @classmethod
    def generate_summary(cls, text, length_mode='medium'):
        """
        Generates an extractive summary from input text.
        Length modes:
            - 'short': ~20% of sentences (min 2, max 5)
            - 'medium': ~35% of sentences (min 3, max 9)
            - 'long': ~50% of sentences (min 5, max 15)
        """
        sentences = cls.split_into_sentences(text)
        if not sentences:
            return {
                'summary_text': "Insufficient text content to generate a meaningful summary.",
                'original_words': len(text.split()),
                'summary_words': 0,
                'reduction_pct': 0,
                'sentence_count': 0
            }

        # If document is very brief, return all sentences
        if len(sentences) <= 3:
            summary = " ".join(sentences)
            return {
                'summary_text': summary,
                'original_words': len(text.split()),
                'summary_words': len(summary.split()),
                'reduction_pct': 0,
                'sentence_count': len(sentences)
            }

        # Calculate word frequencies for non-stopwords
        all_words = cls.tokenize_words(text)
        content_words = [w for w in all_words if w not in STOPWORDS]
        word_freq = Counter(content_words)

        if not word_freq:
            # Fallback if no content words
            selected_sentences = sentences[:3]
            summary = " ".join(selected_sentences)
            return {
                'summary_text': summary,
                'original_words': len(text.split()),
                'summary_words': len(summary.split()),
                'reduction_pct': 0,
                'sentence_count': len(selected_sentences)
            }

        max_freq = max(word_freq.values())
        normalized_freq = {word: count / max_freq for word, count in word_freq.items()}

        # Score each sentence
        scored_sentences = []
        for idx, sentence in enumerate(sentences):
            sentence_words = cls.tokenize_words(sentence)
            if not sentence_words:
                continue

            # Base score: sum of normalized frequencies of content words
            score = sum(normalized_freq.get(w, 0) for w in sentence_words if w in normalized_freq)
            
            # Normalize by sentence length to prevent unfairly favoring overly long sentences
            score = score / (len(sentence_words) ** 0.5)

            # Position bonus: sentences at the start of document/paragraphs carry introductory weight
            if idx == 0:
                score *= 1.3
            elif idx < 3:
                score *= 1.15

            scored_sentences.append((idx, score, sentence))

        # Determine target number of sentences based on length mode
        total_sents = len(scored_sentences)
        if length_mode == 'short':
            target_count = max(2, min(5, int(total_sents * 0.20)))
        elif length_mode == 'long':
            target_count = max(5, min(15, int(total_sents * 0.50)))
        else:  # medium
            target_count = max(3, min(9, int(total_sents * 0.35)))

        target_count = min(target_count, total_sents)

        # Select top scored sentences
        top_sentences = sorted(scored_sentences, key=lambda x: x[1], reverse=True)[:target_count]

        # Re-sort chronologically by their original index to maintain logical reading order
        chronological_sentences = sorted(top_sentences, key=lambda x: x[0])
        summary_text = " ".join(s[2] for s in chronological_sentences)

        original_word_count = len(text.split())
        summary_word_count = len(summary_text.split())
        reduction = round((1 - (summary_word_count / max(original_word_count, 1))) * 100, 1)

        return {
            'summary_text': summary_text,
            'original_words': original_word_count,
            'summary_words': summary_word_count,
            'reduction_pct': max(0.0, reduction),
            'sentence_count': target_count
        }
