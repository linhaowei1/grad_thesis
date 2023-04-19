import json
import os
from sympy import *

sgs = [">=", "<=", ">", "<", "="]
symbol_list = ['a','b','c','f']
a, b, c, f = symbols(' '.join(symbol_list), real=True)

def shift_term_and_simplify(eq):
    for symb in sgs:
        if symb in eq:
            left, right = eq.split(symb)
            left = simplify(left + '-(' + right + ')')
            return str(left).replace(' ','') + symb + '0'

def remove_positive(lst):
    """
    Remove any elements from lst that are of the form A>=0, if there is also an element
    of the form A=0 in the list.

    Args:
        lst: A list of strings representing mathematical expressions.

    Returns:
        A new list with elements removed as described above.
    """
    to_remove = set()
    for i, expr in enumerate(lst):
        if ">=" in expr:
            var, val = expr.split(">=")
            if val == "0" and var + '=0' in lst:
                to_remove.add(i)
    return [expr for i, expr in enumerate(lst) if i not in to_remove]
# def heuristic(objective, premises):

#     for premise in premises:
#         if '>=' in premise or '<=' in premise or '<' in premise or '>' in premise:
#             continue
#         _left, _right = premise.split('=')
#         if _left in symbol_list:
#             objective = objective.replace(_left, '0')

with open('./INT/data/ordered_filed/all.src', 'r') as f:
    lines = f.readlines()
data = []

all_set = set()
for line in lines:
    premise, objective = line.split('to')
    premises = premise.strip().split('&')
    objective = objective.strip()

    objective = shift_term_and_simplify(objective.strip('\n'))
    if 'nan' in str(objective):
        continue
    if 'zoo' in str(objective):
        continue
    premises = list(set(shift_term_and_simplify(eq) for eq in premises))
    if '1>=0' in premises:
        premises.remove('1>=0')
    if '0>=0' in premises:
        premises.remove('0>=0')
    
    if premises[0] is None:
        premises.remove(None)
    premises = remove_positive(premises)

    if 'null' in premises:
        premises.remove('null')
    
    if (' '.join(premises) + objective) in all_set:
        continue
    else:
        all_set.add(' '.join(premises) + objective)

    data.append({'objective': objective, 'premises': premises})

with open('./prompts/dsp.txt', 'r') as f:
    prompt = f.read()


for cnt, item in enumerate(data):
    fn = f'./problems/problem{cnt}.txt'
    with open(fn, 'w') as f:
        f.write(prompt)
        premises = json.dumps(item['premises']).replace('\"','').strip('[]')
        f.write('[premises] {}\n'.format(premises))
        f.write('\n[goal] {}\n'.format(item['objective']))
        f.write('\n[proof]\n')
    
    fn_s = f'./solutions/solution{cnt}.txt'
    with open(fn_s, 'w') as f:
        premises = json.dumps(item['premises']).replace('\"','').strip('[]')
        f.write('[premises] {}\n'.format(premises))
        f.write('\n[goal] {}\n'.format(item['objective']))
        f.write('\n[proof]\n')
