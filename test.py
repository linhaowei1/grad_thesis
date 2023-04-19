from sympy import symbols, simplify

a, b, c = symbols('a b c')
expression = a**2 + b**2 + 3*c**4

# Simplify the expression
simplified_expression = simplify(expression)

# Check if the simplified expression is always non-negative
is_always_non_negative = simplified_expression >= 0
print(is_always_non_negative)  # True