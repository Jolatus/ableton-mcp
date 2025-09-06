import re

NOTES = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}

CHORD_INTERVALS = {
    'maj': [0, 4, 7],
    'min': [0, 3, 7],
    'dim': [0, 3, 6],
    'aug': [0, 4, 8],
    'maj7': [0, 4, 7, 11],
    'min7': [0, 3, 7, 10],
    '7': [0, 4, 7, 10],
    'dim7': [0, 3, 6, 9],
    'm7b5': [0, 3, 6, 10],
    'sus2': [0, 2, 7],
    'sus4': [0, 5, 7],
}

def parse_chord_name(chord_name: str) -> (str, str):
    """
    Parses a chord name like "C#min7" into its root note "C#" and quality "min7".
    Returns a tuple (root, quality).
    Handles major chords which may not have a quality specified (e.g., "C").
    """
    match = re.match(r'(C#|Db|D#|Eb|F#|Gb|G#|Ab|A#|Bb|C|D|E|F|G|A|B)(.*)', chord_name)
    if not match:
        raise ValueError(f"Invalid chord name: {chord_name}")

    root, quality = match.groups()

    if not quality:
        quality = 'maj'

    return root, quality

def chord_to_midi(chord_name: str, octave: int = 4) -> list[int]:
    """
    Converts a chord name into a list of MIDI note numbers.
    """
    try:
        root, quality = parse_chord_name(chord_name)

        if quality not in CHORD_INTERVALS:
            # Attempt to match common variations
            if quality.lower() in ['m', 'minor']:
                quality = 'min'
            elif quality.lower() in ['M', 'major']:
                quality = 'maj'
            elif 'dom' in quality.lower():
                quality = '7'
            else:
                raise ValueError(f"Unknown chord quality: {quality}")

        base_note = NOTES[root] + (octave * 12)
        intervals = CHORD_INTERVALS[quality]

        return [base_note + i for i in intervals]
    except Exception as e:
        raise ValueError(f"Could not parse chord '{chord_name}': {e}")
