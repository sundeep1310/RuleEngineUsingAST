from typing import Dict, Any, List, Union
import logging

class Node:
    def __init__(self, node_type: str, value: Any = None):
        self.type = node_type
        self.value = value
        self.left = None
        self.right = None

def create_rule(rule_string: str) -> Node:
    tokens = tokenize(rule_string)
    
    def parse_expression() -> Node:
        nonlocal tokens
        if not tokens:
            raise ValueError("Unexpected end of expression")
        
        node = parse_condition()
        
        while tokens and tokens[0] in ('AND', 'OR'):
            operator = tokens.pop(0)
            right = parse_condition()
            new_node = Node("operator", operator)
            new_node.left = node
            new_node.right = right
            node = new_node
        
        return node

    def parse_condition() -> Node:
        nonlocal tokens
        if not tokens:
            raise ValueError("Unexpected end of condition")
        
        if tokens[0] == '(':
            tokens.pop(0)  # Remove opening parenthesis
            node = parse_expression()
            if not tokens or tokens.pop(0) != ')':
                raise ValueError("Missing closing parenthesis")
            return node
        else:
            if len(tokens) < 3:
                raise ValueError(f"Incomplete condition: {' '.join(tokens)}. Format should be 'attribute operator value'.")
            attribute = tokens.pop(0)
            operator = tokens.pop(0)
            value = tokens.pop(0)
            
            if operator not in ('=', '>', '<'):
                raise ValueError(f"Invalid comparison operator: '{operator}'. Use '=', '>', or '<'.")
            
            return Node("condition", (attribute, operator, value))

    try:
        result = parse_expression()
        if tokens:  # If there are remaining tokens, the expression is invalid
            remaining = ' '.join(tokens)
            raise ValueError(f"Unexpected tokens at end of expression: '{remaining}'")
        return result
    except Exception as e:
        logging.error(f"Error parsing rule: {str(e)}")
        raise ValueError(f"Invalid rule syntax: {str(e)}")

def tokenize(rule_string: str) -> List[str]:
    rule_string = rule_string.replace('(', ' ( ').replace(')', ' ) ')
    tokens = []
    current_token = ''
    in_quotes = False
    
    for char in rule_string:
        if char == "'" and not in_quotes:
            in_quotes = True
            current_token += char
        elif char == "'" and in_quotes:
            in_quotes = False
            current_token += char
            tokens.append(current_token)
            current_token = ''
        elif char.isspace() and not in_quotes:
            if current_token:
                tokens.append(current_token)
                current_token = ''
        else:
            current_token += char
    
    if current_token:
        tokens.append(current_token)
    
    return tokens

def evaluate_rule(node: Node, data: Dict[str, Any]) -> bool:
    if node.type == "condition":
        attribute, operator, value = node.value
        if attribute not in data:
            logging.warning(f"Attribute '{attribute}' not found in data")
            return False
        
        data_value = data[attribute]
        try:
            if operator == '=':
                return str(data_value) == value.strip("'")
            elif operator == '>':
                return float(data_value) > float(value)
            elif operator == '<':
                return float(data_value) < float(value)
            else:
                raise ValueError(f"Unknown operator: {operator}")
        except ValueError as e:
            logging.error(f"Error comparing values: {data_value} {operator} {value}. Error: {str(e)}")
            return False
        
    elif node.type == "operator":
        left_result = evaluate_rule(node.left, data)
        if node.value == "AND" and not left_result:
            return False
        if node.value == "OR" and left_result:
            return True
        right_result = evaluate_rule(node.right, data)
        if node.value == "AND":
            return left_result and right_result
        elif node.value == "OR":
            return left_result or right_result
        else:
            raise ValueError(f"Unknown operator: {node.value}")
    
    else:
        raise ValueError(f"Unknown node type: {node.type}")

def combine_rules(rules: List[str]) -> Node:
    if not rules:
        return None
    if len(rules) == 1:
        return create_rule(rules[0])
    
    combined = Node("operator", "OR")
    combined.left = create_rule(rules[0])
    combined.right = combine_rules(rules[1:])
    return combined

# Test the functions
if __name__ == "__main__":
    test_cases = [
        {
            "rule": "(age > 30 AND department = 'Sales') OR (salary < 50000)",
            "data": {"age": 35, "department": "Sales", "salary": 60000},
            "expected": True
        },
        {
            "rule": "(age > 30 AND department = 'Sales') OR (salary < 50000)",
            "data": {"age": 25, "department": "Marketing", "salary": 60000},
            "expected": False
        },
        {
            "rule": "(age < 10 AND department = 'Child Labor') OR (salary < 750)",
            "data": {"age": 5, "department": "Child Labor", "salary": 60000},
            "expected": True
        },
        {
            "rule": "(age > 20 AND department = 'Sales') OR (salary < 90000)",
            "data": {"age": 25, "department": "Sales", "salary": 80000},
            "expected": True
        },
        {
            "rule": "age > 30 AND department = 'Sales'",
            "data": {"age": 35, "department": "Marketing", "salary": 60000},
            "expected": False
        }
    ]

    for i, test in enumerate(test_cases, 1):
        try:
            rule_node = create_rule(test["rule"])
            result = evaluate_rule(rule_node, test["data"])
            print(f"\nTest {i}:")
            print(f"Rule: {test['rule']}")
            print(f"Data: {test['data']}")
            print(f"Expected: {test['expected']}, Got: {result}")
            print(f"{'PASSED' if result == test['expected'] else 'FAILED'}")
        except ValueError as e:
            print(f"Test {i} Error: {e}")

    # Test combine_rules
    print("\nTesting combine_rules:")
    rules = [
        "(age < 10 AND department = 'Child Labor') OR (salary < 750)",
        "(age > 30 AND department = 'Sales') OR (salary < 50000)"
    ]
    combined_rule = combine_rules(rules)
    test_data = {"age": 35, "department": "Sales", "salary": 60000}
    result = evaluate_rule(combined_rule, test_data)
    print(f"Combined rules: {rules}")
    print(f"Test data: {test_data}")
    print(f"Result: {result}")
    print("PASSED" if result else "FAILED")