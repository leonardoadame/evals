#!/usr/bin/python3

import ast
from fractions import Fraction

from solve import EquationGenerator

class Vars:
    '''
    Extract variable names from the Python AST tree of an Equation (solve.py).
    '''
    def __init__(self, module):
        lhs_node = module.body[0].targets[0]
        rhs_node = module.body[0].value

        self.lhs = self._get_vars(lhs_node)
        self.rhs = self._get_vars(rhs_node)

        assert len(self.lhs) == 1

        for name in self.lhs:
            self.lhs = name
            break

    def _get_vars(self, tree):
        return {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}

class ValueGenerator:
    '''
    Generate values for the given variables,
    in order to test numerically the correctness of expressions.

    The values cover the range from -5 to +5 in steps of 0.5,
    plus a small offset chosen to minimize the chance of a division by zero:
    for instance, when equations like y = a / (b - x) are generated.
    '''
    def generate(self, rhs_variables):
        yield from self._gen(tuple(rhs_variables), {})

    def _gen(self, variables, values):
        if not variables:
            yield values
            return

        first = variables[0]
        rest  = variables[1:]

        offset = len(rest) + 1
        denominator = EquationGenerator.TOP_PRIME

        for iv in range(-10, 11):
            values[first] = Fraction(offset, denominator) + Fraction(iv, 2)

            yield from self._gen(rest, values)

class Code:
    '''
    Hold the compiled bytecode for an expression.
    '''
    def __init__(self, expr):
        self.expr = ast.parse(expr)
        self.code = self._compile(self.expr)

    def _compile(self, expr):
        return compile(expr, filename='<ast>', mode='exec')

class Evaluator:
    '''
    Test that the correct answer is correct, and the rest are incorrect.

    The test is done by numerically evaluating expressions over a range
    of its variables, using exact rational aritmetic (the "fractions" module).

    (Used internally by ProblemGenerator, problem.py).
    '''
    def __init__(self, eq, answers):
        '''
        Receive the equation (the question) and the available answers,
        as generated by ProblemGenerator._generate.
        '''
        self.question = Code(eq)
        self.answers  = []

        for correct, answer in answers:
            if correct:
                self.correct = len(self.answers)
            self.answers.append(Code(answer))

    def _variables(self):
        '''
        Extract variables from the LHS and RHS side of the equation.

        At this point, the "equation" is actually a Python assignment
        instruction's AST, in self.question.expr.

        Performs sanity checks over these sets of variables.
        '''
        q_vars       = Vars(self.question.expr)
        answers_vars = [Vars(a.expr) for a in self.answers]
        a_vars       = answers_vars[0]

        assert all(a.lhs == a_vars.lhs for a in answers_vars)
        assert all(a.rhs == a_vars.rhs for a in answers_vars)

        assert q_vars.lhs not in q_vars.rhs
        assert a_vars.lhs not in a_vars.rhs
        
        assert (set(q_vars.lhs) | q_vars.rhs) \
            == (set(a_vars.lhs) | a_vars.rhs)

        return q_vars, a_vars

    def test(self):
        '''
        Test the validity of the given answers, both the correct and incorrect ones.
        '''
        q_vars, a_vars = self._variables()

        ok = len(self.answers) * [True]

        self.bad_answers = set()

        v = ValueGenerator()
        for values in v.generate(q_vars.rhs):
            scope = dict(values)

            # Suppose a question and answers are of the form
            #   Q:   v = <expression containing "x", the variable to solve for>
            #   A1:  x = <expression containing "v">
            #   A2:  x = <expression containing "v">
            #   A3:  x = <expression containing "v">
            #   ...
            #
            # For each combination of variable values in the RHS of Q,
            # execute the assignment
            #    v = <expression>

            try:
                exec(self.question.code, scope)
            except ZeroDivisionError:
                continue

            # "expected" is the value of "x", in our example above
            # (one of the RHS values in Q, as generated by ValueGenerator)

            expected = scope[a_vars.lhs]

            for n in range(len(self.answers)):
                if not ok[n]:
                    continue

                # For each answer, evaluate the assignment
                #   x = <expression containing "v">
                # and verify that we obtain back the same value
                # of "x" as "expected"

                del scope[a_vars.lhs]
                try:
                    exec(self.answers[n].code, scope)
                except ZeroDivisionError:
                    # just add something so that it can be deleted
                    # by "del" above in the next iteration
                    scope[a_vars.lhs] = expected
                    continue

                computed = scope[a_vars.lhs]

                check = computed == expected

                if not check:
                    if n == self.correct:
                        self.msg = f'The "correct" answer {n+1} is not correct' \
                                     + f'\n  expected {a_vars.lhs} = {expected}\n  ' \
                                     + '\n  '.join(f'{v} = {scope[v]}' \
                                                   for v in sorted(scope) \
                                                   if len(v) == 1)
                        return False
                    else:
                        ok[n] = False

        # "Incorrect" answers may evaluate correctly by chance
        # for SOME values of the variables, but not for ALL of them

        ret = True
        for n in range(len(ok)):
            if ok[n] and n != self.correct:
                self.bad_answers.add(n)

                self.msg = f'The "wrong" answer {n+1}' \
                             + ' turns out to be correct'
                ret = False

        return ret
