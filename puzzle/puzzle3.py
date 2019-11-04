import sys

#change add_z3_path to True if you wanna add the path to z3 and specify it
add_z3_path = False
path_to_z3 = r'C:\\Users\\Adi\\Desktop\\20160740\\z3-master\\build\\python'
if add_z3_path:
	sys.path.append(path_to_z3)
from z3 import *


def print_assignment(model):
	print("The crate labaled Apple is the " + str(model.evaluate(realApple)) + " crate")
	print("The crate labaled Orange is the " + str(model.evaluate(realOrange)) + " crate")
	print("The crate labaled Mixed is the " + str(model.evaluate(realMixed)) + " crate")

def given_constraints(solver):
	solver.add(Distinct(realApple, realOrange, realMixed))
	solver.add(realApple != crate.apple)
	solver.add(realOrange != crate.orange)
	solver.add(realMixed != crate.mixed)
	solver.add(picked(crate.apple) == fruit.apple)
	solver.add(picked(crate.orange) == fruit.orange)

crate = Datatype('crate')
crate.declare('apple')
crate.declare('orange')
crate.declare('mixed')
crate = crate.create()

fruit = Datatype('fruit')
fruit.declare('apple')
fruit.declare('orange')
fruit = fruit.create()

picked = Function('picked', crate, fruit)

realApple = Const('realApple', crate)
realOrange = Const('realOrange', crate)
realMixed = Const('realMixed', crate)

s = Solver()
given_constraints(s)
s.add(picked(realOrange) == fruit.apple)
if s.check() == sat: #if there's an assignment for problem 3
	model = s.model()
	print("This is one of the assignments")
	print_assignment(model)
	s.add(Or(realApple != model.evaluate(realApple), realOrange != model.evaluate(realOrange), realMixed != model.evaluate(realMixed)))
	if s.check() == sat: #if we negate the given assignment it would produce another one in case it was not unique
		print("The assignment is not unique")
		print("This is another satisfying assignment")
		print_assignment(s.model())
	else: #otherwise it's unique
		print("The assignment is unique")




