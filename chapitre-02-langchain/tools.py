"""myTravel's tools, written for LangChain.

Compare with chapter 1: no JSON schema written by hand. The `@tool`
decorator reads the function name, its type hints and its docstring
and builds the description the model needs. The docstring IS the
manual, so write it for the model, not for yourself.

Three tools call real, free APIs that need no key:
Wikipedia (facts), Open-Meteo (weather), Frankfurter (rates).
"""

import ast
import json
import operator
import urllib.parse
import urllib.request

from langchain.tools import tool

OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub,
             ast.Mult: operator.mul, ast.Div: operator.truediv,
             ast.Pow: operator.pow, ast.USub: operator.neg}


def _get_json(url, params=None):
    """The single network door. Tests replace this function.

    Plain `urllib`, from the standard library: nothing to install,
    and it trusts the system certificate store (corporate proxies).
    """
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    # Wikipedia refuses requests without an identifiable User-Agent.
    agent_name = "agentia-book/1.0 (github.com/btecsec)"
    request = urllib.request.Request(
        url, headers={"User-Agent": agent_name})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


@tool(parse_docstring=True)
def web_search(query: str) -> str:
    """Look up a place, a person or a concept on Wikipedia.

    Use it before answering any factual question about a destination
    (history, size, country, main sights).

    Args:
        query: The page title to look up, for example 'Lisbon'.
    """
    title = query.strip().replace(" ", "_")
    try:
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
        page = _get_json(url + title)
    except OSError as error:
        # A sentence, not an exception: the model adapts to it.
        return f"No result for {query!r} ({error})."
    return page.get("extract") or f"No summary for {query!r}."


@tool(parse_docstring=True)
def calculate(expression: str) -> str:
    """Evaluate arithmetic. Never calculate in your head.

    Args:
        expression: A formula such as '3 * 120 * 1.085'.
    """
    try:
        tree = ast.parse(expression, mode="eval")
        return str(_evaluate(tree.body))
    except (ValueError, SyntaxError, ZeroDivisionError) as error:
        return f"Cannot calculate {expression!r}: {error}"


def _evaluate(node):
    """Accept numbers and + - * / ** only: never eval model text."""
    if isinstance(node, ast.Constant) and isinstance(
        node.value, (int, float)
    ):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        left, right = _evaluate(node.left), _evaluate(node.right)
        return OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](_evaluate(node.operand))
    raise ValueError("only numbers and + - * / ** are allowed")


@tool(parse_docstring=True)
def get_weather(city: str) -> str:
    """Get the current temperature in a city (Open-Meteo data).

    Args:
        city: The city name, for example 'Tokyo'.
    """
    try:
        found = _get_json(
            "https://geocoding-api.open-meteo.com/v1/search",
            {"name": city, "count": 1},
        ).get("results")
        if not found:
            return f"Unknown city {city!r}."
        place = found[0]
        current = _get_json(
            "https://api.open-meteo.com/v1/forecast",
            {
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m",
            },
        )["current"]
    except (OSError, ValueError, KeyError) as error:
        return f"Weather service unavailable ({error})."
    degrees = current["temperature_2m"]
    where = f"{place['name']}, {place['country']}"
    return f"{where}: {degrees} degrees C."


@tool(parse_docstring=True)
def convert_currency(
    amount: float, source: str, target: str
) -> str:
    """Convert an amount between two currencies (real rates).

    Args:
        amount: The amount to convert, for example 250.
        source: The ISO code of the starting currency, e.g. 'EUR'.
        target: The ISO code of the target currency, e.g. 'JPY'.
    """
    try:
        data = _get_json(
            "https://api.frankfurter.dev/v1/latest",
            {"base": source.upper(), "symbols": target.upper()},
        )
        rate = data["rates"][target.upper()]
    except (OSError, ValueError, KeyError) as error:
        return f"Cannot convert {source} to {target} ({error})."
    converted = amount * rate
    code = target.upper()
    return f"{amount} {source.upper()} = {converted:.2f} {code}"


# A "toolkit" is a list of tools handed to the agent together.
TOOLKIT = [web_search, calculate, get_weather, convert_currency]
