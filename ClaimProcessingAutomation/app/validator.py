def validate_claim(data: dict):
    # Placeholder validation logic
    errors = []
    if "claim" not in data:
        errors.append("Missing claim field")
    return (len(errors) == 0, errors)