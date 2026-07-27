def compare_versions(latest: str, current: str) -> int:
    """Compare two version strings.
    
    Returns:
        -1 if latest < current
        0 if latest == current
        1 if latest > current
    """
    try:
        latest_parts = list(map(int, latest.split('.')))
        current_parts = list(map(int, current.split('.')))
        
        max_length = max(len(latest_parts), len(current_parts))
        while len(latest_parts) < max_length:
            latest_parts.append(0)
        while len(current_parts) < max_length:
            current_parts.append(0)
        
        for l, c in zip(latest_parts, current_parts):
            if l > c:
                return 1
            elif l < c:
                return -1
        return 0
    except Exception:
        return 0

def is_newer_version(latest: str, current: str) -> bool:
    """Check if latest version is newer than current."""
    return compare_versions(latest, current) > 0