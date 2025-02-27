#!/usr/bin/python

# Preprocesses tokens describing mental functions from the following ontologies:
#	(1) Cognitive Atlas (Disorders): http://www.cognitiveatlas.org/
#	(2) Mental Disorder Ontology, MFO (Internal): https://github.com/jannahastings/mental-functioning-ontology/tree/master/ontology/internal 
#	(3) MESH (Category F): https://www.ncbi.nlm.nih.gov/mesh


import os, binascii, string
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords


# Load WordNet lemmatizer from NLTK
lemmatizer = WordNetLemmatizer()

# Load English stop words from NLTK
stops = stopwords.words("english")

# Load punctuation from string
punc = string.punctuation


# Function for stemming, conversion to lowercase, and removal of punctuation
def preprocess(token):

	# Encode in UTF-8
	token = token.encode("utf-8")

	# Replace words containing slashes with two forms, one with spaces and one with nothing as replacement
	preproc = []
	if "/" in token:
		preproc.append(token.replace("/", " "))
		preproc.append(token.replace("/", ""))
		parts = token.split("/")
		word1 = parts[0].split()[-1]
		word2 = parts[1].split()[0]
		preproc.append(token.replace(word1, "").replace("/", ""))
		preproc.append(token.replace(word2, "").replace("/", ""))
	if " or " in token:
		preproc.append(token.replace(" or ", " "))
		parts = token.split(" or ")
		word1 = parts[0].split()[-1]
		word2 = parts[1].split()[0]
		preproc.append(token.replace(word1, ""))
		preproc.append(token.replace(word2, ""))
	if "-" in token:
		preproc.append(token.replace("-", ""))
	if ("(") in token:
		parts = token.replace(")", "(").split("(")
		preproc.append(parts[1].strip())
		del parts[1]
		preproc.append("".join(parts).replace("  ", " "))
		preproc.append(token.replace("(", "").replace(")", ""))
	preproc.append(token)

	for i, token in enumerate(preproc): 

		# Convert to lowercase and remove stop words, which contain punctuation
		filtered = []
		for word in token.lower().split():
			if word not in stops:
				word = "".join(char for char in word if char not in punc)
				filtered.append(word)
		text = " ".join(filtered)

		# Perform lemmatization, excluding acronyms and names in lexicon or RDoC
		acronyms = ["abc", "aai", "adhd", "aids", "atq", "asam", "asi", "aqc", "asi", "asq", "ax", "axcpt", "axdpx", "bees", "bas", "bdm", "bis", "bisbas", "beq", "brief", "cai", "catbat", "cfq", "deq", "dlmo", "dospert", "dsm", "dsmiv", "dsm5", "ecr", "edi", "eeg", "eei", "ema", "eq", "fmri", "fne", "fss", "grapes", "hrv", "iri", "isi", "ius", "jnd", "leas", "leds", "locs", "poms", "meq", "mctq", "sans", "ippa", "pdd", "pebl", "pbi", "prp", "mspss", "nart", "nartr", "nih", "npu", "nrem", "pas", "panss", "qdf", "rbd", "rem", "rfq", "sam", "saps", "soc", "srs", "srm", "strain", "suds", "teps", "tas", "tesi", "tms", "ug", "upps", "uppsp", "vas", "wais", "wisc", "wiscr", "wrat", "wrat4", "ybocs", "ylsi"]
		names = ["american", "badre", "barratt", "battelle", "bartholomew", "becker", "berkeley", "conners", "corsi", "degroot", "dickman", "marschak", "beckerdegrootmarschak", "beery", "buktenica", "beerybuktenica", "benton", "bickel", "birkbeck", "birmingham", "braille", "brixton", "california", "cambridge", "cattell", "cattells", "chapman", "chapmans", "circadian", "duckworth", "duckworths", "eckblad", "edinburgh", "erickson", "eriksen", "eysenck", "fagerstrom", "fitts", "gioa", "glasgow", "golgi", "gray oral", "halstead", "reitan", "halsteadreitan", "hamilton", "hayling", "holt", "hooper", "hopkins", "horne", "ostberg", "horneostberg", "iowa", "ishihara", "kanizsa", "kaufman", "koechlin", "laury", "leiter", "lennox", "gastaut", "lennoxgastaut", "london", "macarthur", "maudsley", "mcgurk", "minnesota", "montreal", "morris", "mullen", "muller", "lyer", "mullerlyer", "munich", "parkinson", "pavlovian", "peabody", "penn", "penns", "piaget", "piagets", "pittsburgh", "porteus", "posner", "rey", "ostereith", "reyostereith", "reynell", "rivermead", "rutledge", "salthouse", "babcock", "spielberger", "spielbergers", "stanford", "binet", "shaver", "simon", "stanfordbinet", "sternberg", "stroop", "toronto", "trier", "yale", "brown", "umami", "uznadze", "vandenberg", "kuse", "vernier", "vineland", "warrington", "warringtons", "wason", "wechsler", "wisconsin", "yalebrown", "zimbardo", "zuckerman"]
		lemmas = []
		for word in text.split():
			if word in acronyms + names:
				lemmas.append(word)
			else:
				lemmas.append(lemmatizer.lemmatize(word))
		token = "_".join(lemmas)
		preproc[i] = token

	return preproc


# Initialize lexicon sets and lists
lexicon_set = set()
lexicon_raw = set()
mdo, nifstd, mesh, snomed = [], [], [], []


# Load tokens from:
#	- Cognitive Atlas (disorders)
def load_txt(file, ngram_set):
	for line in open(file, "rU").readlines():
		token = line.strip().lower()
		lexicon_raw.add(token)
		for t in preprocess(token):
			lexicon_set.add(t)

ca_types = ["disorders"]
for type in ca_types:
	load_txt("cognitive-atlas_{}.txt".format(type), lexicon_set)


# Load tokens from MFO
def load_owl(file, ngram_set, owl_list):
	for line in open(file, "rU").readlines():
		if "</rdfs:label>" in line:
			token = line.split(">")[1].replace("</rdfs:label", "").strip().lower()
			if token not in ["inheres_in", "by_means", "has-input", "has_participant", "in_response_to", "is_about", "qualifier"]:
				owl_list.append(token)
				lexicon_raw.add(token)
				for t in preprocess(token):
					lexicon_set.add(t)

load_owl("MD-core.owl", lexicon_set, mdo)
mdo_file = open("MD-core.txt", "w+")
for token in mdo:
	mdo_file.write(token + "\n")
mdo_file.close()


# Load tokens from MeSH
def load_mesh(file, ngram_set, mesh_list):
	records = open(file).read().split("*NEWRECORD\n")
	for record in records:
		if "MN = F" in record:
			entries = [line.replace("ENTRY = ", "").replace("PRINT ", "").split("|")[0].strip() for line in record.split("\n") if "ENTRY = " in line]
			for token in entries:
				if "," in token:
					parts = token.split(", ")
					token = " ".join([parts[1], parts[0]])
				mesh_list.append(token)
				lexicon_raw.add(token)
				for t in preprocess(token):
					lexicon_set.add(t)

load_mesh("MeSH_d2018.bin", lexicon_set, mesh)
mesh_file = open("MeSH_d2018.txt", "w+")
for token in mesh:
	mesh_file.write(token + "\n")
mesh_file.close()


# Export raw ontology lexicon
lexicon_raw = [n + "\n" for n in lexicon_raw]
lexicon_raw.sort()
with open("lexicon_psychiatry.txt", "w+") as raw_file:
	for n in lexicon_raw:
		raw_file.write(n)

# Export preprocessed ontology lexicon
lexicon = list(lexicon_set)
lexicon.sort()
lexicon_file = open("lexicon_psychiatry_preproc.txt", "w+")
for n in lexicon:
	if n != "":
		lexicon_file.write(n + "\n")
lexicon_file.close()