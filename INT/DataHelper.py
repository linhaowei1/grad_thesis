import random
import argparse
import os
from proof_system.prover import Prover
from proof_system.all_axioms import all_axioms_to_prove, generation_type, all_axioms
from proof_system.logic_functions import necessary_logic_functions
from proof_system.numerical_functions import necessary_numerical_functions
from proof_system.utils import is_ls, is_empty_ls, is_entity
from proof_system.all_axioms import generation_type, axiom_sets
from logic.logic import Entity

def valid_combo(combo_names):
    combo_types = [generation_type[name] for name in combo_names]
    equality, inequality, transition = 0, 0, 0
    for combo_type in combo_types:
        if combo_type == "Equality":
            equality += 1
        elif combo_type == "Inequality":
            inequality += 1
        elif combo_type == "Transition":
            transition += 1
        else:
            raise NotImplementedError

    if transition > 1:
        return False
    elif transition == 0 and inequality > 0:
        return False
    else:
        return True

# Divide axioms into the three categories: equal, transitive, and unequal according to their transformation types
def divide_axioms(axiom_names_to_use):
    equal_theorems = [axiom for axiom in axiom_names_to_use if generation_type[axiom] == "Equality"]
    transitive_theorems = [axiom for axiom in axiom_names_to_use if generation_type[axiom] == "Transition"]
    unequal_theorems = [axiom for axiom in axiom_names_to_use if generation_type[axiom] == "Inequality"]
    return equal_theorems, transitive_theorems, unequal_theorems

# Generate an order from a possible combination
def generate_order_from_combination(chosen_axioms, proof_length):
    eq_axioms, transitive_axioms, une_axioms = divide_axioms(chosen_axioms)
    assert len(transitive_axioms) <= 1
    non_transitive_apps = eq_axioms + une_axioms
    random.shuffle(non_transitive_apps)
    if len(chosen_axioms) < proof_length:
        additional_apps = random.choices(non_transitive_apps, k=proof_length - len(chosen_axioms))
    else:
        additional_apps = []
    applications = transitive_axioms + non_transitive_apps + additional_apps

    eq_applications, transitive_applications, une_applications = divide_axioms(applications)
    applications = eq_applications + transitive_applications + une_applications

    return applications

def generate_orders(available_axioms, proof_length, data_size):

    generated_ = 0
    order_list = []

    while generated_ < data_size:
        
        combination = random.sample(list(available_axioms.keys()), k=min(len(available_axioms), proof_length))
        if not valid_combo(combination):
            continue
        try:
            order = generate_order_from_combination(combination, proof_length)
        except IndexError:
            continue
        if not valid_combo(order):
            continue
        order_list.append(order)
        generated_ += 1
    
    return order_list
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_path', required=True, type=str)
    parser.add_argument('--axiom_set', required=True, type=str, default='ordered_field')
    parser.add_argument('--proof_length', required=True, type=int, default=15)
    parser.add_argument('--data_size', required=True, type=int, default=1000)
    args = parser.parse_args()

    if not os.path.isdir(args.data_path):
        os.makedirs(args.data_path)
    
    available_axioms = axiom_sets[args.axiom_set]

    axiom_orders = generate_orders(available_axioms, proof_length=args.proof_length, data_size=args.data_size)

    print(axiom_orders[0])