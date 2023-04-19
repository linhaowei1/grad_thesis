from copy import deepcopy
import os
import re
import sympy
import argparse
import pdb

sgs = [">=", "<=", ">", "<", "="]
symbol_list = ['a','b','c','d']
a, b, c, d = sympy.symbols(' '.join(symbol_list), real=True)
zero_list = set('0')

def clear(obj):
    out = re.sub(r'\/\*.*?\*\/','', obj, flags=re.DOTALL)
    out = out.replace('^', '**')
    out = out.split('\n')
    new_obj = []
    for line in out:
        if line.strip():
            new_obj.append(line)
    return new_obj

def get_ineq(line):
    match = re.search('[<>]=?|=', line)
    if match:
        return match.group()
    else:
        raise NotImplementedError

def get_premises(obj_lst):
    assert obj_lst[0].startswith('[premises]')
    return [x.strip() for x in obj_lst[0].strip('[premises]').split(',')]

def get_goal(obj_lst):
    assert obj_lst[1].startswith('[goal]')
    return obj_lst[1].strip('[goal]').strip()

def check_left_with_goal(left, goal):
    return check_permute(left, goal)

def check_zero(expr):
    expr = str(sympy.simplify(expr)).replace(' ','')
    for zero in zero_list:
        expr = expr.replace(zero, '0')
    return sympy.simplify(expr) == 0

def check_gt_zero(expr, premises):
    expr = str(expr).replace(' ','')
    terms = sympy.simplify(expr).args

    gt_set = {'0'}
    for premise in premises:
        if get_ineq(premise) == '<=' or get_ineq(premise) == '<':
            gt_set.add(str(sympy.simplify('-(' + premise.split(get_ineq(premise))[0] + ')')).replace(' ',''))
        else:
            gt_set.add(str(sympy.simplify(premise.split(get_ineq(premise))[0])).replace(' ',''))
    
    flag = True
    for term in terms:
        if terms in premises:
            continue
        try:
            if terms >= 0:
                continue
        except:
            pass
        
        flag = check_gt_zero(term, premises)
    
    return flag
                    

def check_rewrite(obj, goal=None, premises=None):
    assert len(obj.split('=>')) == 2
    left, right = obj.split('=>')
    left_ineq, right_ineq = get_ineq(left), get_ineq(right)
    
    if premises is not None:
        if not check_left_with_premises([left], premises):
            return False
    else:
        if not check_left_with_goal(left, goal):
            return False

    new_left = left.split(left_ineq)[0] + '-(' + left.split(left_ineq)[1] + ')'
    new_right = right.split(right_ineq)[0] + '-(' + right.split(right_ineq)[1] + ')'

    if left_ineq == '=' and right_ineq == '=':
        if sympy.simplify(new_left) == sympy.simplify(new_right) or \
            sympy.simplify(new_left) == sympy.simplify('-(' + new_right + ')'):
            return True, right
    elif left_ineq == right_ineq and left_ineq != '=':
        if check_zero(sympy.simplify('(' + new_left + ')-(' + new_right + ')')):
            return True, right
        try:
            if sympy.simplify('(' + new_right + ')/(' + new_left + ')') > 0:
                return True, right
        except:
            pass
    elif left_ineq == '>=' and right_ineq == '<=':
        try:
            if sympy.simplify('-(' + new_right + ')/(' + new_left + ')') > 0:
                return True, right
        except:
            pass
    # constant factor
    elif eval(str(sympy.simplify('(' + new_left + ')/(' + new_right +')')).replace(' ','')) > 0:
        return True, right
    
    return False, right

def check_substitute(obj, premise, goal=None, premises=None):
    assert len(obj.split('=>')) == 2
    left, right = obj.split('=>')

    if premises is not None:
        check_left_with_premises([left], premises)
    else:
        check_left_with_goal(left, goal)

    left_ineq, right_ineq = get_ineq(left), get_ineq(right)
    
    if left_ineq != right_ineq:
        raise NotImplementedError
    pre_left, pre_right = premise.split('=')
    pre_right = '(' + pre_right + ')'
    substitue_left = left.replace(' ','').replace(pre_left, pre_right)
    return sympy.simplify(substitue_left) == sympy.simplify(right), right

def check_permute(expr1, expr2):
    ineq1, ineq2 = get_ineq(expr1), get_ineq(expr2)
    expr1 = expr1.split(ineq1)[0].strip()
    expr2 = expr2.split(ineq2)[0].strip()
    if ineq1 == ineq2:
        return sympy.simplify(expr1 + '-(' + expr2 + ')') == 0
    else:
        raise NotImplementedError

def check_left_with_premises(left_lst, premises):
    for left in left_lst:

        if left.replace(' ','') in premises:
            continue
        
        ## if every symbol has positive exp
        check = False
        
        if get_ineq(left) == '>=':
            check_expr = left.split('>=')[0].strip()

        for item in sympy.simplify(check_expr).args:
            check = True
            try:
                if item > 0:
                    continue
            except:
                _tmp = str(item).split('**')
                if len(_tmp) == 2 and eval(_tmp[-1]) % 2 == 0:
                    continue
            check = False
            break
        
        if check:
            continue
        
        args = [x for x in sympy.simplify(check_expr).args if not str(x).isdigit()]
        for premise in premises:
            pre_args = [x for x in sympy.simplify(premise.split(get_ineq(premise))[0]).args if not str(x).isdigit()]
            
            if len(pre_args) == 0:
                pre_args = [sympy.simplify(premise.split(get_ineq(premise))[0])]
            if pre_args == args:
                try:
                    if check_permute(left, premise):
                        check = True
                        break
                except:
                    _left_ineq = get_ineq(left)
                    _premise_ineq = get_ineq(premise)
                    try:
                        if _premise_ineq == '=':
                            _premise_left, _premise_right = premise.split(_premise_ineq)
                            new_premise = str(sympy.simplify(sympy.simplify(left.split(_left_ineq)[0]))).replace(_premise_left, _premise_right)
                            if bool(new_premise + _left_ineq + left.split(_left_ineq)[1]):
                                check = True
                                print(f"[SYMPY]::Add {premise} => {left} into proof lines.")
                                break
                    except:
                        continue
        
        return False
    return True

def check_implication(obj, premises):
    assert len(obj.split('=>')) == 2
    left, right = obj.split('=>')
    left_lst = [x.strip() for x in left.split(',')]
    
    check_left_with_premises(left_lst, premises)

    if len(left_lst) >= 2:
        left_ineq_lst = [get_ineq(x) for x in left_lst]
        right_ineq = get_ineq(right)
        if len(set(left_ineq_lst)) == 1 and left_ineq_lst[0] == '>=' and right_ineq == '>=':
            left_left_exp_lst = [x.split('>=')[0].strip() for x in left_lst]
            left_right_exp_lst = [x.split('>=')[1].strip() for x in left_lst]
            right_left_exp, right_right_exp = right.split('>=')

            if right_right_exp.replace(' ','') == '0' and check_gt_zero(right_left_exp, left_lst):
                return True, right
            
            # x >= y, y >= z => x >= z
            elif (sympy.simplify(left_right_exp_lst[0]) == sympy.simplify(left_left_exp_lst[1]) \
            and sympy.simplify(right_left_exp) == sympy.simplify(left_left_exp_lst[0])\
            and sympy.simplify(right_right_exp) == sympy.simplify(left_right_exp_lst[1])) or \
            (sympy.simplify(left_right_exp_lst[1]) == sympy.simplify(left_left_exp_lst[0]) \
            and sympy.simplify(right_left_exp) == sympy.simplify(left_left_exp_lst[1])\
            and sympy.simplify(right_right_exp) == sympy.simplify(left_right_exp_lst[0])):
                return True, right
    elif len(left_lst) == 1:
        left, right = obj.split('=>')
        left_ineq, right_ineq = get_ineq(left), get_ineq(right)
        if left_ineq != right_ineq:
            raise NotImplementedError
        new_left = left.split(left_ineq)[0] + '-(' + left.split(left_ineq)[1] + ')'
        new_right = right.split(right_ineq)[0] + '-(' + right.split(right_ineq)[1] + ')'
        if eval(str(sympy.simplify('(' + new_left + ')/(' + new_right +')')).replace(' ','')) > 0:
            return True, right
    else:
        raise NotImplementedError

def simple(obj):
    ineq = get_ineq(obj)
    left, right = obj.split(ineq)
    return str(sympy.simplify(left + '-(' + right + ')')).replace(' ','').replace('**','^') + ineq + '0'

def check_done(premises, goal):

    for premise in premises:
        ineq = get_ineq(premise)
        lhs, rhs = premise.split(ineq)
        if ineq == '=' and sympy.simplify(rhs) == 0:
            zero_list.add(str(sympy.simplify(lhs)).replace(' ',''))
            zero_list.add(str(sympy.simplify('-' + '(' + lhs+ ')')).replace(' ',''))

    if goal == '0>=0' or goal == '0<=0' or goal == '0==0': 
        return True, premises, goal
    if goal in premises:
        print(f"SYMPY:: find the goal in premises.")
        return True, premises, goal
    
    # TODO: heuristic, can be deleted
    simple_obj = simple(goal)
    
    if simple_obj == '0>=0' or simple_obj == '0<=0' or simple_obj == '0==0': 
        print(f"SYMPY:: the goal can be simplified to {simple_obj}.")
        return True, premises, goal
    
    if simple_obj in premises:
        goal = simple(goal)
        print(f"SYMPY:: simplify goal to {goal}.")
        return True, premises, goal
    return False, premises, goal

def rewrite_by_sympy(obj):
    assert len(obj.split('=>')) == 2
    left, _ = obj.split('=>')
    left_ineq = get_ineq(left)
    new_left = left.split(left_ineq)[0] + '-(' + left.split(left_ineq)[1] + ')'
    new_expr = left + ' => ' + str(sympy.simplify(new_left.replace(' ',''))).replace(' ','') + left_ineq + '0'
    return new_expr.replace('**','^')

def main(args):

    solution = os.path.join('solutions_15', args.solution)
    with open(solution, 'r') as f:
        obj_lst = clear(f.read())

    print('\n'.join(obj_lst))
    premises, goal = get_premises(obj_lst), get_goal(obj_lst)

    # begin solution
    assert obj_lst[2] == '[proof]'
    ptr = 3
    solved = False

    while True:
                
        solved, premises, goal = check_done(premises, goal)

        if ptr >= len(obj_lst) or obj_lst[ptr].startswith('[DONE]') or solved:
            break

        line = obj_lst[ptr]

        if len(line.split(']:')) != 2:
            raise NotImplementedError
        
        # object type
        if line.startswith('premise'):
            first_part = 'premise'
        elif line.startswith('goal'):
            first_part = 'goal'
        else:
            raise NotImplementedError
        
        # operation type
        second_part = line.split(']:')[0].split('[')[1]
        third_part = line.split(']:')[1].strip()

        if second_part == 'rewrite':
            if first_part == 'goal':
                rewrite_ok, right = check_rewrite(third_part, goal=goal)
            else:
                rewrite_ok, right = check_rewrite(third_part, premises=premises)
            if not rewrite_ok:
                _rewrite = rewrite_by_sympy(third_part)
                if _rewrite.replace(" ","") != third_part.replace(" ","") and \
                _rewrite.split("=>")[0].replace(' ','') != _rewrite.split('=>')[1].replace(' ',''):
                    new_line = first_part + ' [' + second_part + ']: ' + rewrite_by_sympy(third_part)
                    print(f"SYMPY::the {obj_lst[ptr]} can be modified as:\n{new_line}")
                else:
                    print(f"SYMPY::you don't need to rewrite here...")
                break
            else:   # TODO: left may be out of premises.
                right = right.replace(' ','')
                print(f'rewrite in line [{ptr}] is correct! Add {right} into {first_part}.')
                if first_part.startswith('p'):
                    premises.append(right)
                else:
                    goal = right
                ptr += 1
                continue

        elif '=' in second_part:
            if second_part not in premises:
                raise NotImplementedError

            if first_part == 'goal':
                substitute_ok, right = check_substitute(third_part, second_part, goal=goal)
            else:
                substitute_ok, right = check_substitute(third_part, second_part, premises=premises)
            if not substitute_ok:
                lhs, _ = third_part.split('=>')
                l, l_new = second_part.split('=')
                lhs_new = (lhs.replace(' ','').replace(l, '(' + l_new + ')'))
                print(f'substitue in line [{ptr}] should be {lhs} => {lhs_new}.')
                break
            else:
                right = right.replace(' ','')
                print(f'substitute in line [{ptr}] is correct! Add {right} into {first_part}.')
                if first_part.startswith('p'):
                    premises.append(right)
                else:
                    goal = right
                ptr += 1
                continue
        
        elif second_part == 'imply':
            imply_ok, right = check_implication(third_part, premises)
            if not imply_ok:
                raise NotImplementedError
            else:
                right = right.replace(' ','')
                print(f'implication in line [{ptr}] is correct! Add {right} into {first_part}.')
                if first_part.startswith('p'):
                    premises.append(right)
                else:
                    goal = right
                ptr += 1
                continue

    if solved:
        print('Congratulations! The proof is solved!')
    else:
        print('sorry. The proof is not solved.')
    
    return solved


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--solution', type=str, default=None)
    args = parser.parse_args()
    if args.solution is not None:
        main(args)
    else:
        cnt = 0
        false = []
        for i in range(100):
            args.solution = 'solution{}.txt'.format(i)
            try:
                if main(args):
                    cnt += 1
                else:
                    false.append(i)
            except:
                false.append(i)
                continue
        print("tot correct:", cnt)
        print("false:", false)