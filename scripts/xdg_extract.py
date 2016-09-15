import xmltodict
import json
import pprint
import os

def find_node_in_list(root,serializerID,type="@serializerID"):
	if type in root:
		if root[type] == serializerID:
			return root
			
	for e in root:
		res = find_node(e,serializerID,type)
		if res is not None:
			return res

def find_node(root,serializerID,type="@serializerID"):	
	if type in root:
		if root[type] == serializerID:
			return root
	for e in root:
		if isinstance(root[e], dict):
			res = find_node(root[e],serializerID,type)
			if res is not None:
				return res
		elif isinstance(root[e], list):
			res = find_node_in_list(root[e], serializerID, type)
			if res is not None:
				return res

def populate_predicate(jstring, interpretation, predicates):
	frame_name = interpretation["@name"]
	predicates[frame_name] = {}
	#get lexical unit
	lu_lemmas = []
	for elem in interpretation["constituentList"].split():
		lu_lemmas.append(find_node(jstring, elem)["@surface"])
	predicates[frame_name]["lu"]=" ".join(lu_lemmas)

	#get arguments
	if isinstance(interpretation["ARGS"]["sem_arg"], list):
		for arg in interpretation["ARGS"]["sem_arg"]:
			element = arg["@entity"]
			l = arg["constituentList"].split()
			arg_lemmas=[]
			for elem in l:
				arg_lemmas.append(find_node(jstring, elem)["@surface"])
			predicates[frame_name][element] = arg_lemmas
	
	elif isinstance(interpretation["ARGS"]["sem_arg"], dict):
		arg = interpretation["ARGS"]["sem_arg"]
		element = arg["@entity"]
		l = arg["constituentList"].split()
		arg_lemmas=[]
		for elem in l:
			arg_lemmas.append(find_node(jstring, elem)["@surface"])
		predicates[frame_name][element] = arg_lemmas

def find_predicates(toparse):
	jstring = json.loads(json.dumps(xmltodict.parse(toparse), indent=4))
	interpretation_list = jstring["TEXT"]["PARAGRAPHS"]["P"]["XDGS"]["XDG"]["interpretations"]["interpretationList"]
	predicates = {}
	if interpretation_list is not None:
		interpretation_list = jstring["TEXT"]["PARAGRAPHS"]["P"]["XDGS"]["XDG"]["interpretations"]["interpretationList"]["item"]
		if isinstance(interpretation_list, list):
			for interpretation in interpretation_list:
				populate_predicate(jstring, interpretation, predicates)
		elif isinstance(interpretation_list, dict):
			populate_predicate(jstring, interpretation_list, predicates)
	return predicates
	
def get_sentence(jstring):
	return jstring["TEXT"]["PARAGRAPHS"]["P"]["SUR"]

def read_xdg(path):
	print "Opening: " + path
	toparse = ""
	for l in open(path, "r"):
		toparse = toparse + l
	return json.loads(json.dumps(xmltodict.parse(toparse), indent=4))


#pp = pprint.PrettyPrinter(indent=1)

#dir="comandi_xdg"
#for file in os.listdir(dir):
#    if file.endswith(".xml"):        
#		jstring = read_xdg(dir+"/" + file)
#		print "SENTENCE: " + get_sentence(jstring)
#		predicates = find_predicates(jstring)
#		pp.pprint(predicates)