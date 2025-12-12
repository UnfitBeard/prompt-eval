# utils/helpers.py
import re
from typing import Optional
from datetime import datetime


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    # Convert to lowercase
    text = text.lower()

    # Remove special characters
    text = re.sub(r'[^\w\s-]', '', text)

    # Replace spaces and underscores with hyphens
    text = re.sub(r'[\s_]+', '-', text)

    # Remove consecutive hyphens
    text = re.sub(r'-+', '-', text)

    # Remove leading/trailing hyphens
    text = text.strip('-')

    return text


def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp for display"""
    now = datetime.utcnow()
    diff = now - timestamp

    if diff.days > 365:
        return f"{diff.days // 365} year(s) ago"
    elif diff.days > 30:
        return f"{diff.days // 30} month(s) ago"
    elif diff.days > 0:
        return f"{diff.days} day(s) ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600} hour(s) ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60} minute(s) ago"
    else:
        return "Just now"


def calculate_level(xp: int) -> tuple:
    """Calculate user level based on XP"""
    levels = [
        (0, "Beginner", 0),
        (1000, "Intermediate", 1),
        (5000, "Advanced", 2),
        (15000, "Expert", 3),
        (50000, "Master", 4)
    ]

    for threshold, name, level in reversed(levels):
        if xp >= threshold:
            next_threshold = next(
                (t for t, _, _ in levels if t > threshold), None)
            progress = (xp - threshold) / (next_threshold -
                                           threshold) if next_threshold else 1.0
            return name, level, progress

    return "Beginner", 0, xp / 1000
