import json
from jsonschema import validate, ValidationError

class DSLSchemaValidator:
    def __init__(self, schema_path):
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)

    def validate(self, dsl_json_string):
        try:
            dsl_data = json.loads(dsl_json_string)
            validate(instance=dsl_data, schema=self.schema)
            return True, None
        except json.JSONDecodeError as e:
            return False, f"JSON Decode Error: {e}"
        except ValidationError as e:
            return False, f"Schema Validation Error: {e.message}"
