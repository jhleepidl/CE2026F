"""Shared schemas and accounting exceptions; keep unchanged."""

def object_schema(properties):
    return {"type": "object", "properties": properties, "required": list(properties),
            "additionalProperties": False}

def validate_json(value, schema):
    """Also validate fixture data locally; schema correctness is not task correctness."""
    from jsonschema import validate
    validate(value, schema)
    return value

class BudgetExceeded(RuntimeError):
    pass

class ResponseFailure(RuntimeError):
    pass
