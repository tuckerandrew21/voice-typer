"""
Text processing pipeline for MurmurTone.
Handles custom dictionary, filler removal, and voice commands.
"""
import re


# Voice command mappings
PUNCTUATION_COMMANDS = {
    "period": ".",
    "full stop": ".",
    "comma": ",",
    "question mark": "?",
    "exclamation point": "!",
    "exclamation mark": "!",
    "colon": ":",
    "semicolon": ";",
    "dash": "-",
    "hyphen": "-",
    "open quote": '"',
    "close quote": '"',
    "open parenthesis": "(",
    "close parenthesis": ")",
    "ellipsis": "...",
}

# Words that could be nouns (need position-based heuristics)
AMBIGUOUS_PUNCTUATION = {"period", "colon", "dash", "hyphen"}

STRUCTURE_COMMANDS = {
    "new line": "\n",
    "newline": "\n",
    "new paragraph": "\n\n",
}

EDITING_COMMANDS = {
    "scratch that",
    "delete that",
    "undo that",
}

# Filler words (always removed)
FILLER_WORDS = {"um", "uh", "er", "ah", "hmm", "mm"}

# Multi-word filler phrases (always removed)
FILLER_PHRASES = [
    "you know",
    "i mean",
    "sort of",
    "kind of",
]


class TranscriptionHistory:
    """
    Track recent transcriptions for "scratch that" functionality.
    Stores text and character count for backspace deletion.
    """

    def __init__(self, max_entries=10):
        self.entries = []  # List of (text, char_count)
        self.max_entries = max_entries

    def add(self, text):
        """Add a transcription to history."""
        if text:
            char_count = len(text)
            self.entries.append((text, char_count))
            if len(self.entries) > self.max_entries:
                self.entries.pop(0)

    def get_last_length(self):
        """Return character count of last entry for backspace deletion."""
        if self.entries:
            return self.entries[-1][1]
        return 0

    def pop_last(self):
        """Remove and return last entry."""
        if self.entries:
            return self.entries.pop()
        return None

    def clear(self):
        """Clear all history."""
        self.entries = []


def apply_custom_dictionary(text, dictionary):
    """
    Apply custom dictionary replacements.
    Longer phrases processed first to avoid partial matches.

    Args:
        text: Input text
        dictionary: List of {"from": str, "to": str, "case_sensitive": bool}

    Returns:
        Text with replacements applied
    """
    if not dictionary:
        return text

    # Sort by length (longest first) to handle overlapping patterns
    sorted_dict = sorted(dictionary, key=lambda x: len(x.get("from", "")), reverse=True)

    for entry in sorted_dict:
        source = entry.get("from", "")
        target = entry.get("to", "")
        case_sensitive = entry.get("case_sensitive", False)

        if not source:
            continue

        # Use word boundaries to avoid partial matches
        if case_sensitive:
            pattern = r'\b' + re.escape(source) + r'\b'
            text = re.sub(pattern, target, text)
        else:
            pattern = r'\b' + re.escape(source) + r'\b'
            text = re.sub(pattern, target, text, flags=re.IGNORECASE)

    return text


def remove_fillers(text, aggressive=False, custom_fillers=None):
    """
    Remove filler words from text.

    Conservative mode (default): Only removes obvious fillers (um, uh, er, ah, hmm)
    Aggressive mode: Also removes context-sensitive fillers like "like"

    Args:
        text: Input text
        aggressive: If True, remove context-sensitive fillers
        custom_fillers: Additional filler words to remove

    Returns:
        Text with fillers removed
    """
    if not text:
        return text

    # Build filler set
    fillers = FILLER_WORDS.copy()
    if custom_fillers:
        fillers.update(word.lower() for word in custom_fillers)

    # First pass: Remove multi-word filler phrases
    for phrase in FILLER_PHRASES:
        # Match whole phrase with word boundaries, case-insensitive
        pattern = r'\b' + re.escape(phrase) + r'\b'
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Second pass: Remove single-word fillers
    words = text.split()
    result = []

    for i, word in enumerate(words):
        # Strip punctuation for comparison
        word_clean = word.lower().strip('.,!?;:')

        # Always remove basic fillers
        if word_clean in fillers:
            continue

        # Handle "like" in aggressive mode
        if aggressive and word_clean == "like":
            # Check context: is it likely a filler?
            prev_word = words[i - 1].lower().rstrip('.,!?;:') if i > 0 else ""
            next_word = words[i + 1].lower().strip('.,!?;:') if i + 1 < len(words) else ""

            # Filler patterns:
            # - After comma: "it was, like, amazing"
            # - After "was/were/am/is": quotative "like" (he was like)
            # - Before adjectives/adverbs (harder to detect reliably)
            prev_ends_comma = words[i - 1].endswith(',') if i > 0 else False
            quotative_verbs = {'was', 'were', 'am', 'is', "i'm", "he's", "she's", "it's"}

            if prev_ends_comma or prev_word in quotative_verbs:
                continue  # Skip this "like" (remove it)

        result.append(word)

    # Clean up: remove multiple spaces and trim
    cleaned = ' '.join(result)
    # Remove spaces before punctuation that might result from removal
    cleaned = re.sub(r'\s+([.,!?;:])', r'\1', cleaned)
    # Remove multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)

    return cleaned.strip()


def process_voice_commands(text):
    """
    Process voice commands in transcribed text.

    Handles:
    - Punctuation: "period" -> "."
    - Structure: "new line" -> "\\n"
    - Editing: "scratch that" -> signals deletion

    Args:
        text: Input text

    Returns:
        Tuple of (processed_text, should_scratch)
        If should_scratch is True, the last transcription should be deleted.
    """
    if not text:
        return text, False

    words = text.split()
    result = []
    i = 0
    should_scratch = False

    def strip_punctuation(word):
        """Strip leading/trailing punctuation from a word."""
        return word.strip('.,!?;:"\'-()[]{}')

    while i < len(words):
        # Check for multi-word commands first (2-word phrases)
        if i + 1 < len(words):
            two_word = f"{strip_punctuation(words[i])} {strip_punctuation(words[i + 1])}".lower()

            # Check editing commands (scratch that, delete that)
            if two_word in EDITING_COMMANDS:
                # Remove everything before this and signal scratch
                result = []
                should_scratch = True
                i += 2
                continue

            # Check structure commands (new line, new paragraph)
            if two_word in STRUCTURE_COMMANDS:
                # Attach to previous word without space
                if result:
                    result[-1] = result[-1].rstrip() + STRUCTURE_COMMANDS[two_word]
                else:
                    result.append(STRUCTURE_COMMANDS[two_word])
                i += 2
                continue

            # Check punctuation commands (question mark, exclamation point)
            if two_word in PUNCTUATION_COMMANDS:
                # Attach to previous word without space (strip existing punctuation to avoid duplicates)
                if result:
                    result[-1] = result[-1].rstrip().rstrip('.,!?;:') + PUNCTUATION_COMMANDS[two_word]
                else:
                    result.append(PUNCTUATION_COMMANDS[two_word])
                i += 2
                continue

        # Single word commands - strip punctuation for matching
        word_clean = strip_punctuation(words[i]).lower()

        # Check single-word punctuation commands
        if word_clean in PUNCTUATION_COMMANDS:
            should_convert = True

            # For ambiguous words (period, colon, etc.), use position heuristics
            if word_clean in AMBIGUOUS_PUNCTUATION:
                is_end = (i == len(words) - 1)
                # Check if next word suggests this is a command (sentence-starting word)
                next_word = strip_punctuation(words[i + 1]).lower() if i + 1 < len(words) else ""
                next_is_structure = next_word in {"and", "but", "so", "then", "the", "a", "i", "new", "it", "we", "he", "she", "they", "this", "that"}

                # Only treat as punctuation if at end OR followed by sentence-starting word
                should_convert = is_end or next_is_structure

            if should_convert:
                # Attach to previous word without space (strip existing punctuation to avoid duplicates)
                if result:
                    result[-1] = result[-1].rstrip().rstrip('.,!?;:') + PUNCTUATION_COMMANDS[word_clean]
                else:
                    result.append(PUNCTUATION_COMMANDS[word_clean])
                i += 1
                continue

        # Not a command - keep the word
        result.append(words[i])
        i += 1

    # Join and clean up spaces after newlines
    output = ' '.join(result)
    output = output.replace('\n ', '\n')  # Remove space after newline
    return output, should_scratch


def process_text(text, config, history=None):
    """
    Main entry point for text processing pipeline.

    Pipeline order:
    1. Custom dictionary (convert phonetic mishearings)
    2. Filler removal (clean up before command processing)
    3. Voice commands (process user intent)

    Args:
        text: Raw transcription text
        config: App configuration dict
        history: TranscriptionHistory instance (optional, for scratch that)

    Returns:
        Tuple of (processed_text, should_scratch, scratch_length)
        - processed_text: Final processed text
        - should_scratch: True if "scratch that" was detected
        - scratch_length: Number of characters to delete (if scratching)
    """
    if not text:
        return text, False, 0

    processed = text

    # Step 1: Custom dictionary replacements
    dictionary = config.get("custom_dictionary", [])
    if dictionary:
        processed = apply_custom_dictionary(processed, dictionary)

    # Step 2: Filler removal
    if config.get("filler_removal_enabled", True):
        aggressive = config.get("filler_removal_aggressive", False)
        custom_fillers = config.get("custom_fillers", [])
        processed = remove_fillers(processed, aggressive, custom_fillers)

    # Step 3: Voice commands
    should_scratch = False
    scratch_length = 0

    if config.get("voice_commands_enabled", True):
        processed, should_scratch = process_voice_commands(processed)

        # Handle scratch that
        if should_scratch and config.get("scratch_that_enabled", True) and history:
            scratch_length = history.get_last_length()
            history.pop_last()

    return processed, should_scratch, scratch_length
