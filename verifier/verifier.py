import sys

#	chances are you don't need to change anything here, it's here just in case
# add_x_path is True if it's needed be to added to some path 
# and if you add it specify it here
add_z3_path = False
add_rt_path = False
path_to_rt = r'C:\\"Program Files"\\Java\jdk1.8.0_171\jre\lib\rt.jar'
path_to_z3 = r'C:\\Users\\Adi\\Desktop\\20160740\\z3-master\\build\\python'
windows = False # False if run on a Unix-like system
print_parsed_lines = False # if True it'd print lines after parsing

if add_z3_path:
	sys.path.append(path_to_z3)

from z3 import *

separator = ":"
if windows:
	separator = ";"

argv = sys.argv[1]
os.system("javac " + argv)
arg = argv.replace(".java", "")

if add_rt_path:
	os.system("java -cp ./sootclasses-trunk-jar-with-dependencies.jar soot.Main -cp " + path_to_rt + separator + \
". -output-dir . -output-format shimple -print-tags -keep-line-number -p jb use-original-names:true " + arg)
else:
	os.system("java -cp ./sootclasses-trunk-jar-with-dependencies.jar soot.Main -cp . -output-dir . -output-format shimple -print-tags -keep-line-number -p jb use-original-names:true " + arg)

f = open(arg + ".shimple", "r")
lines = f.readlines()
i = 0

#delete empty lines
while i < len(lines):
	if lines[i].isspace():
		del(lines[i])
	i = i + 1

delete = True
j = 0
while True:
	if "testMe" in lines[j] and "public" in lines[j] and "int" in lines[j]:
		del(lines[j])
		delete = False
		continue

	if "}" in lines[j]:
		delete = True

	if delete or "@parameter" in lines[j] or "z0" in lines[j] or "Test" in lines[j] or \
	"/*" in lines[j] or "{" in lines[j] or "@this" in lines[j] or "java.lang" in lines[j]:
		del(lines[j])
	else:
		j = j + 1

	if j == len(lines):
		break

p = open("child.py", "w+")
p.write("import sys\n")
if add_z3_path:
	p.write("sys.path.append('" + path_to_z3 + "')\n")
p.write("from z3 import *\n")
p.write("s = Solver()\n")

# look for int l1, l2, ... and parse it. I assume nothing else starts with int
# at least not before the first intended one and all declarations are in single line
for k in range(len(lines)): 
	if "int" == lines[k].split()[0]: 
		lines[k] = lines[k].replace("int ", "").replace("$", "").replace(";", "").replace("\n", "").replace("#", "_").strip().split(", ")
		for i in range(len(lines[k])):
			p.write(lines[k][i] + " = Int('" + lines[k][i] + "')\n")
		del(lines[k])
		break

# look for byte l4_1, ... and parse it. I assume nothing else starts with byte
# at least not before the first intended one and all declarations are in single line
for k in range(len(lines)): 
	if "byte" == lines[k].split()[0]:	
		lines[k] = lines[k].replace("byte", "").replace("$", "").replace(";", "").replace("\n", "").replace("#", "_").strip().split(", ")
		for i in range(len(lines[k])):
			p.write(lines[k][i] + " = Int('" + lines[k][i] + "')\n")
		del(lines[k])
		break

def Add(arg):
	p.write("s.add(" + arg +")\n")

# remove not needed characters and replace # with _ as it can't be in a variables name
for i in range(len(lines)): 
	lines[i] = lines[i].strip().replace(";", "").replace("$", "").replace(":", "").replace("#", "_")


leap_count = 0 # used to create new variables for goto statements 
leap_conds = [] # used to bind leaps to their labels
collection = [] # list of active leaps
for i in range(len(lines)):
	line = lines[i].split()
	first_word = line[0]
	offset = 0
	first_chars = list(first_word)
	# offset = 1 if there's this kind of thing at the beginning: (0)
	if len(first_chars) > 2: 
		if first_chars[0] == "(" and first_chars[-1] == ")":
			offset = 1

	#I assume if "if" and "goto" appears then it's the if cond goto labelx line
	if "if" in lines[i] and "goto" in lines[i]: 
		cond = "leap" + str(leap_count)
		leap_count = leap_count + 1
		p.write(cond + " = Bool('" + cond + "')\n")

		if len(collection) == 0:
			Add("(" + line[1 + offset] + " " + line[2 + offset] + " " + line[3 + offset] + ") == Not(" + cond + ")")
		elif len(collection) == 1:
			Add("Implies(" + collection[0] + ", (" + line[1 + offset] + " " + line[2 + offset] + " " + line[3 + offset] + ") == Not(" + cond + "))")
			Add("Implies(Not(" + collection[0] + "), " + cond + ")")
		else:
			Add("Implies(And(" + ", ".join(collection) + "), (" + line[1 + offset] + " " + line[2 + offset] + " " + line[3 + offset] + ") == Not(" + cond + "))")
			Add("Implies(Not(And(" + ", ".join(collection) + ")), " + cond + ")")

		collection.append(cond)

		if offset == 1:
			index = "".join(first_chars[1:-1])
			phi = "phi" + index
			p.write(phi + " = Bool('" + phi + "')\n")
			Add("Not(" + cond + ") == " + phi)

		found = False
		for k in range(len(leap_conds)):
			if (leap_conds[k][0] == line[5 + offset]):	
				leap_conds[k][1].append(cond)
				found = True
				break

		if not found:
			leap_conds.append((line[5 + offset], [cond]))

	elif "label" in first_word:
		# remove everything related to the label, because its scope was escaped
		for k in range(len(leap_conds)): 
			if (leap_conds[k][0] == first_word):
				for t in range(len(leap_conds[k][1])):
					collection.remove(leap_conds[k][1][t])
				del(leap_conds[k])
				break

	# this is where assignments like l1 = l2 + l3 are parsed
	elif ("+" in lines[i] or "-" in lines[i] or "*" in lines[i] or "/" in lines[i]) and len(line) > 4:
		if len(collection) == 0:  
			Add(line[0 + offset] + " == " + line[2 + offset] + " " + line[3 + offset] + " " + line[4 + offset])
		elif len(collection) == 1:
			Add("Implies(" + collection[0] + ", " + line[0 + offset] + " == " + line[2 + offset] + " " + line[3 + offset] + " " + line[4 + offset] + ")")
		else:
			Add("Implies(And(" + ", ".join(collection) + "), " + line[0 + offset] + " == " + line[2 + offset] + " " + line[3 + offset] + " " + line[4 + offset] + ")")
		
		if offset == 1: #phi
			index = "".join(first_chars[1:-1])
			phi = "phi" + index
			p.write(phi + " = Bool('" + phi + "')\n")
			if len(collection) == 0:
				Add(phi + " == True")
			elif len(collection) == 1:
				Add(collection[0] + " == " + phi)
			else:
				Add("And(" + ", ".join(collection) + ") == " + phi)
			

	elif line[offset] == "goto": # this is used to parse lines like goto label2
		cond = "leap" + str(leap_count)
		leap_count = leap_count + 1
		p.write(cond + " = Bool('" + cond + "')\n")

		if len(collection) == 0: #leap
			Add(cond + " == False")
		elif len(collection) == 1:
			Add(collection[0] + " == Not(" + cond + ")")
		else:
			Add("And(" + ", ".join(collection) + ") == Not(" + cond + ")")
		
		if offset == 1: #phi
			index = "".join(first_chars[1:-1])
			phi = "phi" + index
			p.write(phi + " = Bool('" + phi + "')\n")
			Add("Not(" + cond + ") == " + phi)

		collection.append(cond)
		found = False
		for k in range(len(leap_conds)):
			if (leap_conds[k][0] == line[1 + offset]):	
				leap_conds[k][1].append(cond)
				found = True
				break
		if not found:
			leap_conds.append((line[1 + offset], [cond]))

	# this is where assignments like l2 = l1 are parsed
	elif len(line) == (3 + offset) and line[1 + offset] == "=": 
		if len(collection) == 0:
			Add(line[0 + offset] + " == " + line[2 + offset])
		elif len(collection) == 1:
			Add("Implies(" + collection[0] + ", " + line[0 + offset] + " " + " == " + line[2 + offset] + ")")
		else:
			Add("Implies(And(" + ", ".join(collection) + "), " + line[0 + offset] + " " + " == " + line[2 + offset] + ")")
		
		if offset == 1:
			index = "".join(first_chars[1:-1])
			phi = "phi" + index
			p.write(phi + " = Bool('" + phi + "')\n")
			if len(collection) == 0:
				Add(phi + " == True")
			elif len(collection) == 1:
				Add(collection[0] + " == " + phi)
			else:
				Add("And(" + ", ".join(collection) + ") == " + phi)

	#This is supposed to identify the phi line
	elif "Phi(" in lines[i]: 
		line = lines[i].replace("Phi(", "").replace(")", "").replace("=", "").split()
		for k in range(2, len(line), 2):
			Add("Implies(phi" + line[k].replace("_", "").replace(",", "") + ", " + line[0] + " == " + line[k - 1] + ")")

	elif "throw" == first_word:
		if len(collection) == 0:
			print("No jumps to jump over the throw expression?")
			print("Well that means it's unsatisfiable")
		elif len(collection) == 1:
			Add("Implies(Not(" + collection[0] + "), True == False)");
		else:
			Add("Implies(Not(And(" + ", ".join(collection) + ")), True == False)")

	elif "return" == first_word:
		break

p.write("if s.check() == sat:\n")
p.write(" print(s.model())\n")
p.write("else:\n")
p.write(" print('VALID')\n")
p.close()

import child #this is supposed to execute child.py


if print_parsed_lines:
	for i in range(len(lines)):
		print(lines[i])



