import json
import random
import argparse
from copy import deepcopy
from collections import OrderedDict
import shutil
import pickle
import numpy as np
from joblib import Parallel, delayed
import os
from proof_system.prover import Prover
from proof_system.all_axioms import all_axioms_to_prove, generation_type, all_axioms
from proof_system.logic_functions import necessary_logic_functions
from proof_system.numerical_functions import necessary_numerical_functions
from proof_system.utils import is_ls, is_empty_ls, is_entity, all_different_subtrees, get_entity_from_ls_and_coding, EmptyLogicStatement, get_entity_coding_from_ls
from proof_system.all_axioms import generation_type, axiom_sets
from proof_system.graph_seq_conversion import Parser
from logic.logic import Entity
import random
import torch
from data_generation.combos_and_orders import (
    get_combo_order_info, randomize_one_axiom_order,
    generate_order_from_combination
)
from data_generation.forward2backward import forward_to_backward
from data_generation.generate_problems import \
    get_a_forward_problem
from data_generation.utils import (
    initialize_prover, generate_valid_steps, proof_agrees_with_specs,
    steps_valid, valid_combo
)

proof_parser = Parser()


def generate_problem__single_trial(num_axioms, length, train_test, **kwargs):
    """
    Based on INT::generate_problem(), tries to generate problem once. The
    problem with original function is that it needs to get large set of
    combinations/orders as input, since some of them might be invalid.
    """

    avoid_objective_names = kwargs.get("avoid_objective_names", [])
    # Get combos or orders ready
    use_combos, use_orders, k_combos, kl_orders, available_indices = \
        get_combo_order_info(num_axioms, length, train_test, **kwargs)
    # Initialize the atomic entities and the proof
    atom_ents, prover = initialize_prover(**kwargs)

    done = False
    returned_steps = None
    for _ in [0]:
        axiom_order = randomize_one_axiom_order(use_combos, use_orders, k_combos, kl_orders, available_indices, length)
        forward_steps = get_a_forward_problem(atom_ents, prover, axiom_order, **kwargs)
        if forward_steps is None:
            continue
        try:
            # Convert the proof to backward and validate it
            returned_steps = generate_valid_steps(forward_to_backward(forward_steps))
        except TypeError:
            continue
        # Check if the proof generated satisfies the specifications given
        if not proof_agrees_with_specs(returned_steps, length, axiom_order, avoid_objective_names):
            continue
        done = True
        steps_valid(returned_steps)

    if not done:
        returned_steps = None
    return returned_steps


def sample_axiom_order(proof_length, available_axioms):
    # based on INT::generate_combinations_and_orders()
    order = None
    while True:
        combination = random.choices(
            list(available_axioms.keys()),
            k=min(proof_length, len(available_axioms))
        )
        if not valid_combo(combination):
            continue
        try:
            order = generate_order_from_combination(
                combination, proof_length, use_tuple=True)
        except IndexError:
            continue
        if not valid_combo(order):
            continue
        break
    return order

def set_rnd_seed_and_generate_problem(
    seed, proof_length, available_axioms
):

    random.seed(seed)
    n_axioms = min(proof_length, len(available_axioms))
    problem = None
    while problem is None:
        order = sample_axiom_order(proof_length, available_axioms)
        problem = generate_problem__single_trial(
            length=proof_length,
            num_axioms=n_axioms,
            backward=True,
            transform_gt=True,  # check this
            degree=0,  # suspicious
            num_order_or_combo=1,
            orders={f"k{n_axioms}l{proof_length}": [order]},
            train_test='train',
        )
    #last_proof_step = compute_final_statement(problem)
    #problem.append(last_proof_step)

    return problem

def get_available_axioms(axiom_set_name="ordered_field"):
    """
    Args:
        axiom_set_name: which axioms set to use, available values:
        "field" generates equalities only
        "ordered_field": generates equalities and inequalities
    """
    return axiom_sets[axiom_set_name]


def generate_problems(
    n_proofs, n_workers=4, proof_length=5, seed=None,
):
    problems = []

    n_rem_proofs = n_proofs - len(problems)
    np.random.seed(seed)
    if seed is not None:
        torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    seeds = rng.integers(low=0, high=2**63, size=n_rem_proofs)

    problems.extend(
        Parallel(n_jobs=n_workers, verbose=9)(
            delayed(set_rnd_seed_and_generate_problem)(
                seed=seed,
                proof_length=proof_length,
                available_axioms=get_available_axioms(),
            ) for seed in seeds)
    )
    assert len(problems) == n_proofs
    return problems

def convert_proof_to_seq2seq(steps):
    sources, targets = list(), list()
    for i, step in enumerate(steps):
        source, target = proof_parser.parse_proof_step_to_seq(step)
        sources.append(source)
        targets.append(target)
    return sources, targets


def generate_multiple_seq2seq(multiple_problems, all_sources_to_targets=None):
    if not all_sources_to_targets:
        all_sources_to_targets = dict()

    all_src, all_tgt = [], []
    for problem in multiple_problems:
        sources, targets = convert_proof_to_seq2seq(problem)
        all_src.append(sources)
        all_tgt.append(targets)
    return all_src, all_tgt

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_path', required=True, type=str)
    parser.add_argument('--axiom_set', required=True, type=str, default='ordered_field')
    parser.add_argument('--proof_length', required=True, type=int, default=15)
    parser.add_argument('--data_size', required=True, type=int, default=1000)
    args = parser.parse_args()

    if os.path.isdir(args.data_path):
        shutil.rmtree(args.data_path)
    os.makedirs(args.data_path)
    
    problems = generate_problems(args.data_size, n_workers=10, proof_length=args.proof_length, seed=2023)

    pickle.dump(problems, open(os.path.join(args.data_path, "problems.pkl"), "wb"))

    all_src, all_tgt = generate_multiple_seq2seq(multiple_problems=problems)

    with open(os.path.join(args.data_path, "all.src"), "w") as src_out:
        with open(os.path.join(args.data_path, "all.tgt"), "w") as tgt_out:
            for idx, src in enumerate(all_src):
                src_out.write(src[0] + '\n')
