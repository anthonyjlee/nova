import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def ensure_serializable(data):
    """Ensure data is JSON serializable.
    
    Args:
        data: Data to check/convert
        
    Returns:
        JSON serializable version of the data
    """
    try:
        # Convert data to string if it's not a basic type
        if not isinstance(data, (dict, list, str, int, float, bool, type(None))):
            data = str(data)
        elif isinstance(data, dict):
            # Handle dictionary values recursively
            return {k: ensure_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            # Handle list values recursively
            return [ensure_serializable(v) for v in data]
        # Verify it can be serialized
        json.dumps(data)
        return data
    except (TypeError, ValueError) as e:
        logger.error(f"Data is not JSON serializable: {str(e)}")
        return str(data)

def test_function():
    pass

# Test with function object
data = {'handler': test_function}
print('Testing with function object:')
result = ensure_serializable(data)
print(f'Result: {result}')
print(f'Can serialize result: {json.dumps(result) is not None}')

# Test with basic types
data = {'number': 42, 'string': 'hello', 'list': [1,2,3], 'bool': True, 'null': None}
print('\nTesting with basic types:')
result = ensure_serializable(data)
print(f'Result: {result}')
print(f'Can serialize result: {json.dumps(result) is not None}')

# Test with nested non-serializable objects
class TestClass:
    def __str__(self):
        return "TestClass instance"

data = {
    'nested': {
        'obj': TestClass(),
        'list': [1, TestClass(), 3],
        'basic': 'hello'
    }
}
print('\nTesting with nested non-serializable objects:')
result = ensure_serializable(data)
print(f'Result: {result}')
print(f'Can serialize result: {json.dumps(result) is not None}')
