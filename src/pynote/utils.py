# src/pynote/utils.py
"""
Utility functions for PyNote editor.
"""

import os
import json
from pathlib import Path


def get_config_dir():
    """
    Get the configuration directory for PyNote.
    
    Returns:
        Path: Configuration directory path
    """
    if os.name == 'nt':  # Windows
        config_dir = Path(os.environ.get('APPDATA', '')) / 'PyNote'
    else:  # macOS/Linux
        config_dir = Path.home() / '.config' / 'pynote'
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def load_settings():
    """
    Load settings from JSON file.
    
    Returns:
        dict: Settings dictionary
    """
    config_file = get_config_dir() / 'settings.json'
    default_settings = {
        'theme': 'light',
        'autosave': False,
        'autosave_interval': 300,  # seconds
        'tab_size': 4,
        'font_family': 'Courier New',
        'font_size': 12,
        'recent_files': [],
    }
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            # Merge with defaults to handle missing keys
            default_settings.update(settings)
            return default_settings
        except Exception:
            return default_settings
    
    return default_settings


def save_settings(settings):
    """
    Save settings to JSON file.
    
    Args:
        settings: Settings dictionary
    """
    config_file = get_config_dir() / 'settings.json'
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"Failed to save settings: {e}")


def count_words(text):
    """
    Count words in text.
    
    Args:
        text: Text string
    
    Returns:
        int: Word count
    """
    return len(text.split())


def count_chars(text):
    """
    Count characters in text (excluding trailing newline).
    
    Args:
        text: Text string
    
    Returns:
        int: Character count
    """
    return len(text.rstrip('\n'))


def detect_encoding(filepath):
    """
    Detect file encoding (basic implementation).
    
    Args:
        filepath: Path to file
    
    Returns:
        str: Encoding name (defaults to 'utf-8')
    """
    try:
        # Try UTF-8 first
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read()
        return 'utf-8'
    except UnicodeDecodeError:
        # Fallback to latin-1
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                f.read()
            return 'latin-1'
        except Exception:
            return 'utf-8'


    def full_text_search(root_path, pattern, *, regex=False, ignore_case=True, file_extensions=None, recursive=True, context_lines=1):
        """
        Search for a pattern across files under `root_path` and return context-aware matches.

        Args:
            root_path (str or Path): Directory to search in.
            pattern (str): Substring or regex pattern to search for.
            regex (bool): If True, treat `pattern` as a regular expression.
            ignore_case (bool): Case-insensitive search when True.
            file_extensions (iterable[str] | None): If provided, only search files
                with these extensions (e.g., ['.py', '.md']). Extensions should
                include the leading dot.
            recursive (bool): Whether to recurse into subdirectories.
            context_lines (int): Number of lines of context to include before and after match.

        Returns:
            list of dict: Each match is a dict with keys: `path`, `line_no`, `line`,
                          `match`, `pre_context`, `post_context`.
        """
        import re
        from pathlib import Path

        root = Path(root_path)
        if not root.exists():
            raise FileNotFoundError(f"Search root not found: {root}")

        flags = re.IGNORECASE if ignore_case else 0
        matcher = re.compile(pattern, flags) if regex else None

        results = []
        iterator = root.rglob('*') if recursive else root.glob('*')

        for p in iterator:
            if not p.is_file():
                continue
            if file_extensions is not None:
                if p.suffix not in file_extensions:
                    continue
            try:
                enc = detect_encoding(p)
                # Read all lines so we can provide context easily
                with open(p, 'r', encoding=enc, errors='replace') as f:
                    lines = [ln.rstrip('\n') for ln in f]

                for i, line in enumerate(lines, start=1):
                    if regex:
                        m = matcher.search(line)
                        if m:
                            start = m.start()
                            matched = m.group(0)
                        else:
                            continue
                    else:
                        hay = line.lower() if ignore_case else line
                        needle = pattern.lower() if ignore_case else pattern
                        idx = hay.find(needle)
                        if idx == -1:
                            continue
                        start = idx
                        matched = line[start:start + len(pattern)]

                    pre_start = max(0, i - 1 - context_lines)
                    post_end = min(len(lines), i + context_lines)
                    pre_context = lines[pre_start:i - 1]
                    post_context = lines[i:post_end]

                    results.append({
                        'path': str(p),
                        'line_no': i,
                        'line': line,
                        'match': matched,
                        'pre_context': pre_context,
                        'post_context': post_context,
                    })
            except Exception:
                # skip files we can't read
                continue

        return results

