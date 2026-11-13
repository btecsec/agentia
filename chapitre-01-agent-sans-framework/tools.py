"""The agent's tools: fake, on purpose.

A tool is two things:
1. a Python function that YOUR code runs;
2. a description that THE MODEL reads.

The model never sees your function, only its description. Write it
carefully: it is the model's only manual. The tools are fake (three
facts, simulated weather) so every run gives the same answers and
the tests need no network.
"""

import ast
import operator

# The "web" of this chapter: three facts, enough to see search work.
KNOWLEDGE_BASE = {
    "tokyo": "Tokyo: 14 million people, capital of Japan, UTC+9.",
    "lisbon": "Lisbon: 550,000 people, capital of Portugal, UTC+0.",
    "kyoto": "Kyoto: 1.4 million people, imperial capital to 1868.",
}
WEATHER = {
    "tokyo": "18 degrees C, light rain",
    "lisbon": "24 degrees C, sunny",
    "kyoto": "16 degrees C, cloudy",
}
# Only these operators are allowed in `calculate`. Never eval() text
# written by a model: it could run anything.
OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub,
             ast.Mult: operator.mul, ast.Div: operator.truediv,
             ast.Pow: operator.pow, ast.USub: operator.neg}


def search(query):
    """Look up a city in the fake knowledge base."""
    for city, fact in KNOWLEDGE_BASE.items():
        if city in query.lower():
            return fact
    # A sentence, not an exception: the model reads it and adapts.
    known = ", ".join(KNOWLEDGE_BASE)
    return f"Nothing found for {query!r}. Known: {known}."


def calculate(expression):
    """Evaluate basic arithmetic, safely."""
    try:
        tree = ast.parse(expression, mode="eval")
        return str(evaluate(tree.body))
    except (ValueError, SyntaxError, ZeroDivisionError) as error:
        return f"Cannot calculate {expression!r}: {error}"


def evaluate(node):
    """Walk the syntax tree: numbers and operators, nothing else."""
    if isinstance(node, ast.Constant) and type(node.value) in (
            int, float):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        left, right = evaluate(node.left), evaluate(node.right)
        return OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](evaluate(node.operand))
    raise ValueError("only numbers and + - * / ** are allowed")


def get_weather(city):
    """Return the (simulated) weather in a city."""
    forecast = WEATHER.get(city.strip().lower())
    if forecast is None:
        known = ", ".join(WEATHER)
        return f"No weather for {city!r}. Known: {known}."
    return f"Weather in {city}: {forecast}."


# Catalogue: the name the model says -> the Python function to run.
TOOLS = {"search": search, "calculate": calculate,
         "get_weather": get_weather}


def schema(name, description, parameter, parameter_description):
    """One tool description, in the dialect OpenRouter speaks."""
    return {"type": "function", "function": {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": {parameter: {
                "type": "string",
                "description": parameter_description}},
            "required": [parameter],
        },
    }}


TOOL_SCHEMAS = [
    schema("search", "Find facts about a city: population, "
           "country, time zone. Use it before answering about a "
           "place.",
           "query", "The city to look up, for example 'Tokyo'."),
    schema("calculate", "Evaluate an arithmetic expression. Never "
           "calculate in your head: use this tool.",
           "expression", "A formula such as '14 * 3 + 2'."),
    schema("get_weather", "Get the current weather in a city.",
           "city", "The city name, for example 'Lisbon'."),
]
