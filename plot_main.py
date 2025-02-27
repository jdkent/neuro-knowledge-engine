#!/usr/bin/python3

"""plot_main.py: Generates plots in the main text of 'A computational knowledge engine for human neuroscience'"""

__author__	  	= "Elizabeth Beam"
__email__ 		= "ebeam@stanford.edu"
__copyright__   = "Copyright 2021, Elizabeth Beam"
__license__	 	= "MIT"
__version__		= "1.0.1"

# Version 1.0.1: 
#   - Runs on atlas of 118 regions with cerebellar substructures.
#   - Uses 'protoype' in place of 'archetype' in script and variable names.
#   - Computes modularity and generalizability within discovery and replication splits.


# Built-in python modules
import argparse
import collections
import os

# Computing and machine learning modules
import numpy as np
import pandas as pd
import sklearn

# Modules in this repository 
import utilities
from style import style
from ontology import ontology
from prediction import evaluation
from partition import partition
from prototype import prototype
from modularity import modularity
from mds import mds


# Arguments for customizing analyses and plots
parser = argparse.ArgumentParser(description="Generate plots for 'A computational knowledge engine for human neuroscience'")
parser.add_argument("--v_vsm", type=int, default=190428, help="Version of GloVe embeddings (YYMMDD)")
parser.add_argument("--v_dtm", type=int, default=190325, help="Version of document-term matrix (YYMMDD)")
parser.add_argument("--v_rdoc", type=int, default=190124, help="Version of RDoC matrix (YYMMDD)")
parser.add_argument("--clf", type=str, default="lr", help="Classification architecture ('lr' for logistic regression, 'nn' for neural network)")
parser.add_argument("--n_circuits", default=range(2,51), help="Range for number of data-driven circuits to generate")
parser.add_argument("--n_terms", default=range(5,26), help="Range of number of terms per data-driven domains")
parser.add_argument("--n_domains", type=int, default=6, help="Number of domains selected for the data-driven ontology")
parser.add_argument("--ord_domains", type=list, default=[6,4,5,1,3,2], help="Order for the selected domains in the data-driven ontology")
parser.add_argument("--n_iter", type=int, default=1000, help="Number of iterations for bootstrap and null distributions")
parser.add_argument("--n_iter_fw", type=int, default=10000, help="Number of iterations for RDoC and DSM framework generation analyses")
parser.add_argument("--ci", type=float, default=0.999, help="Confidence interval for plotting distributions")
parser.add_argument("--alpha", type=float, default=0.001, help="Significance level for statistical tests")
parser.add_argument("--font", type=str, default="style/Arial Unicode.ttf", help="Font for plots")
args = parser.parse_args()


################################################
############### 0. Load the data ###############
################################################

print("\n--- LOADING THE DATA")

# Path to basic input data
data_path = "data"

# Framework variables for iterating and plotting
frameworks = ["data-driven", "rdoc", "dsm"] # Frameworks to analyze
titles = {"data-driven": "data-driven", "rdoc": "RDoC", "dsm": "DSM"} # For printing and plotting
suffixes = {"data-driven": "", "rdoc": "_opsim", "dsm": "_opsim"} # For framework files 
clfs = {"data-driven": "_" + args.clf, "rdoc": "", "dsm": ""} # Classifier used to generate framework
clf2name = {"lr": "logistic_regression", "nn": "neural_network"} # Full names for classification architectures
directions = ["forward", "reverse"] # Directions for classification

# Text and activation coordinate inputs
dtm = utilities.load_doc_term_matrix(version=args.v_dtm, binarize=True, path=data_path) # Document-term matrix
act = utilities.load_coordinates(path=data_path) # Activation coordinates

# PubMed IDs (PMIDs) for articles
pmids = act.index.intersection(dtm.index)
dtm = dtm.loc[pmids]
act = act.loc[pmids]

# Splits of the PMIDs into train, validation, and test sets
splits = {split: [int(pmid.strip()) for pmid in open("{}/splits/{}.txt".format(data_path, split))] 
				  for split in ["train", "validation", "test"]}

# Atlas for brain circuit plots
atlas = utilities.load_atlas(path=data_path)


################################################
##### 1. Generate the data-driven ontology #####
################################################

print("\n--- GENERATING THE DATA-DRIVEN ONTOLOGY")

# Path to ontology inputs and outputs
ontol_path = "ontology/"

# Load the lexicon of terms for mental functions
lexicon = utilities.load_lexicon(["cogneuro"], path="lexicon", tkn_filter=dtm.columns)

# Compute the PMI-weighted structure-term matrix
stm = ontology.load_stm(act.loc[splits["train"]], dtm.loc[splits["train"], lexicon]) 

# Generate the data-driven domains over the specified ranges
for k in args.n_circuits:

	# Cluster structures by PMI-weighted co-occurrences with functions
	circuit_file = "{}circuits/circuits_k{:02d}.csv".format(ontol_path, k)
	if not os.path.isfile(circuit_file):
		clust = ontology.cluster_structures(k, stm, act.columns)
		clust.to_csv(circuit_file, index=None)

	# Assign functions to circuits by post-biserial correlation of occurrences
	list_file = "{}lists/lists_k{:02d}.csv".format(ontol_path, k)
	if not os.path.isfile(list_file):
		print("Assigning functions")
		clust = pd.read_csv(circuit_file, index_col=None)
		lists = ontology.assign_functions(k, clust, splits, act, dtm, lexicon, list_lens=args.n_terms)
		lists.to_csv(list_file, index=None)

# Evaluate the classifiers used to select the optimal number of domains
fits = ontology.load_fits(args.clf, directions, args.n_circuits, path=ontol_path)
features = ontology.load_domain_features(dtm, act, directions, args.n_circuits, 
										 suffix="_" + args.clf, path=ontol_path)
stats = ontology.compute_eval_stats(args.clf, directions, args.n_circuits, features, fits, 
									splits["validation"], n_iter=args.n_iter, path=ontol_path)

# Plot evaluation metrics
for direction, shape in zip(directions+["mean"], [">", "<", "D"]):
	ontology.plot_scores_by_k(direction, args.n_circuits, stats, shape=shape, op_k=args.n_domains, 
							  interval=args.ci, font=args.font, path=ontol_path, clf=args.clf, print_fig=False)

# Name the domains
lists, circuits = ontology.load_ontology(args.n_domains, path=ontol_path, suffix="_" + args.clf)
k2name = ontology.name_domains(lists, dtm, path="")
names = [k2name[k] for k in args.ord_domains]

# Export the named domains
lists, circuits = ontology.export_ontology(lists, circuits, args.n_domains, args.ord_domains, args.clf, 
										   act, k2name, path=ontol_path)

# Plot the term lists
print("\n------ Plotting word clouds")
ontology.plot_wordclouds("data-driven", names, lists, metric="R", path="{}figures/lists/".format(ontol_path),
						 suffix="_" + args.clf, palette=style.palettes["data-driven"], height=350, width=260, 
						 min_font_size=0, max_font_size=50, n_offsets=25,
						 brightness_offset=0.15, darkness_offset=-0.35, print_fig=False)

# Plot the brain circuits
print("\n------ Plotting circuit maps")
scores = utilities.score_lists(lists, dtm, label_var="DOMAIN").loc[act.index]
pmi = ontology.compute_cooccurrences(act, scores, positive=True)
pmi = ontology.threshold_pmi_by_circuits(pmi, circuits)
utilities.map_plane(pmi, atlas, "{}figures/circuits/data-driven_{}".format(ontol_path, args.clf), 
		  			plane="z", cmaps=style.colormaps["data-driven"], cbar=True, 
		  			suffix="_z", verbose=False, print_fig=False)


################################################
###### 2. Generate the expert frameworks #######
################################################

# Filter out terms from the DTM if they did not occur in the corpus
dtm_fw = utilities.load_doc_term_matrix(version=args.v_dtm, binarize=False, path=data_path)
dtm_fw = dtm_fw.loc[:, (dtm_fw != 0).any(axis=0)]
dtm_fw = utilities.doc_mean_thres(dtm_fw)


###### RDoC ######
print("\n--- GENERATING THE RDOC FRAMEWORK")

# Load the vector space model, which is GloVe trained on 29,828 general neuroimaging articles
vsm_rdoc = pd.read_csv("{}/text/glove_gen_n100_win15_min5_iter500_{}.txt".format(data_path, args.v_vsm), 
					   index_col=0, header=None, sep=" ")

# Load the seed terms and domains from the RDoC matrix
seeds_rdoc = pd.read_csv("lexicon/rdoc_{}/rdoc_seeds.csv".format(args.v_rdoc), index_col=None, header=0)
seeds_rdoc = seeds_rdoc.loc[seeds_rdoc["TOKEN"].isin(vsm_rdoc.index)]
doms_rdoc = style.order["rdoc"]

# Add RDoC seeds to the lexicon and filter out terms that did not occur in the DTM or VSM
lex_rdoc = set(lexicon).union(seeds_rdoc["TOKEN"])
lex_rdoc = sorted(list(lex_rdoc.intersection(dtm_fw.columns).intersection(vsm_rdoc.index)))

# Generate term lists that maximize semantic similarity to the centroid of seeds in each domain
lists_rdoc = ontology.load_rdoc_lists(lex_rdoc, vsm_rdoc, seeds_rdoc, dtm_fw, n_terms=args.n_terms, path=ontol_path)

# Compare similarity to seeds in each domain between this approach and that of McCoy et al.
print("\n------ Plotting similarity to seeds")
stats = ontology.compute_rdoc_similarity(doms_rdoc, seeds_rdoc, lists_rdoc, vsm_rdoc, 
										 n_iter=args.n_iter_fw, interval=args.ci, path=ontol_path)
ontology.plot_rdoc_similarity(doms_rdoc, stats, font=args.font, path=ontol_path)

# Plot the term lists
print("\n------ Plotting word clouds")
ontology.plot_wordclouds("rdoc", doms_rdoc, lists_rdoc, path="{}figures/lists/".format(ontol_path),
						 metric="SIMILARITY", palette=style.palettes["rdoc"], height=350, width=260, 
						 min_font_size=0, max_font_size=50, n_offsets=25,
						 brightness_offset=0.15, darkness_offset=-0.35, print_fig=False)

# Plot the brain circuits
print("\n------ Plotting circuit maps")
circuits_rdoc = ontology.load_framework_circuit(lists_rdoc, dtm, act, "rdoc")
utilities.map_plane(circuits_rdoc, atlas, "{}figures/circuits/rdoc".format(ontol_path), 
	  				cmaps=style.colormaps["rdoc"], plane="z", cbar=True, cut_coords=None,
	  				suffix="_z", verbose=False, print_fig=False)


###### DSM ######
print("\n--- GENERATING THE DSM FRAMEWORK")

# Load the vector space model, which is GloVe trained on 26,070 psychiatric neuroimaging articles
vsm_dsm = pd.read_csv("{}/text/glove_psy_n100_win15_min5_iter500_{}.txt".format(data_path, args.v_vsm), 
					  index_col=0, header=None, sep=" ")

# Load the seed terms and domains from the DSM-5
seeds_dsm = pd.read_csv("{}/text/seeds_dsm5.csv".format(data_path), index_col=None, header=0)
doms_dsm = style.order["dsm"]

# Load the lexicon of psychiatric terms and filter out terms that did not occur in the DTM or VSM
lex_dsm = utilities.load_lexicon(["cogneuro", "dsm", "psychiatry"], path="lexicon")
lex_dsm = sorted(list(set(lex_dsm).intersection(vsm_dsm.index).intersection(dtm_fw.columns)))

# Generate term lists that maximize semantic similarity to the centroid of seeds in each domain
lists_dsm = ontology.load_dsm_lists(lex_dsm, vsm_dsm, seeds_dsm, n_terms=args.n_terms, path=ontol_path)

# Threshold domains by those with one or more terms in >5% of articles with coordinate data
doms_dsm_filt = []
for dom in doms_dsm: 
	tkns = set(lists_dsm.loc[lists_dsm["DOMAIN"] == dom, "TOKEN"])
	freq = sum([1.0 for doc in dtm_fw[tkns].sum(axis=1) if doc > 0]) / float(len(dtm_fw))
	if freq > 0.05:
		doms_dsm_filt.append(dom)

# Export DSM term lists with frequency-thresholded domains
lists_dsm = lists_dsm.loc[lists_dsm["DOMAIN"].isin(doms_dsm_filt)]
lists_dsm = lists_dsm.loc[lists_dsm["DISTANCE"] > 0]
lists_dsm.to_csv("{}lists/lists_dsm_opsim.csv".format(ontol_path), index=None)

# Plot the term lists
print("\n------ Plotting word clouds")
ontology.plot_wordclouds("dsm", doms_dsm, lists_dsm, path="{}figures/lists/".format(ontol_path),
						 metric="SIMILARITY", palette=style.palettes["dsm"], height=350, width=260, 
						 min_font_size=0, max_font_size=50, n_offsets=25,
						 brightness_offset=0.15, darkness_offset=-0.35,  print_fig=False)

# Plot the brain circuits
print("\n------ Plotting circuit maps")
circuits_dsm = ontology.load_framework_circuit(lists_dsm, dtm, act, "dsm")
utilities.map_plane(circuits_dsm, atlas, "{}figures/circuits/dsm".format(ontol_path), 
	  				cmaps=style.colormaps["dsm"], plane="z", cbar=True, cut_coords=None,
	  				suffix="_z", verbose=False, print_fig=False)


################################################
########## 3. Assess reproducibility ###########
################################################

print("\n--- ASSESSING REPRODUCIBILITY")

# Path to reproducibility analysis outputs
rep_path = "prediction/"
clf_path = rep_path + clf2name[args.clf] + "/"

# Evaluation metrics to be computed in the test set
metric_labels = ["rocauc", "f1"] 

# Brain structure labels
struct_labels = pd.read_csv("{}/brain/labels.csv".format(data_path), index_col=2)
struct_labels = struct_labels.loc[act.columns, "ABBREVIATION"].values

# Parameters for plotting evaluation metrics
axis_labels = {"forward": struct_labels, "reverse": []}
figsize = {"forward": (13,3.2), "reverse": (3.6,3.2)}
ylim = {"rocauc": [0.4,0.8], "f1": [0.3,0.7]}
dxs = {"forward": {"data-driven": 0.55, "rdoc": 0.55, "dsm": 0.55}, 
	   "reverse": {"data-driven": 0.11, "rdoc": 0.11, "dsm": 0.17}}
opacity = {"forward": 0.4, "reverse": 0.65}

# Initialize the dictionary for statistics
rep_stats_keys = ["obs", "boot", "null", "null_ci", "p", "fdr"]
rep_stats = {stat: {} for stat in rep_stats_keys}

for framework in frameworks:

	print("\n------ Processing the {} framework".format(titles[framework]))

	# Add the framework to the dictionary of statistics
	for stat in rep_stats_keys:
		rep_stats[stat][framework] = {}

	# Load the classifier inputs and labels
	lists, circuits = utilities.load_framework(framework, clf=clfs[framework], 
											   suffix=suffixes[framework], path=ontol_path)
	scores = utilities.score_lists(lists, dtm)
	domains = list(circuits.columns)
	index = {"forward": act.columns, "reverse": domains}

	# Color brain structures by the domain with highest weight
	palette = {"forward": [], "reverse": style.palettes[framework]}
	for structure in act.columns:
		dom_idx = np.argmax(circuits.loc[structure].values)
		color = palette["reverse"][dom_idx]
		palette["forward"].append(color)

	# Load fits and data specific to the classification architecture
	fits = {}
	for direction in directions:
		fits[direction] = evaluation.load_fit(args.clf, framework, direction, path=rep_path)
		X, Y = evaluation.load_dataset(args.clf, scores, act, splits["test"])

	# Compute and plot evaluation metrics
	for direction, data in zip(directions, [[X, Y], [Y, X]]):
		features, labels = data
		pred_probs, preds = evaluation.load_predictions(args.clf, fits[direction], features)
		fpr, tpr = evaluation.compute_roc(labels, pred_probs)
		evaluation.plot_curves("roc", framework, direction, fpr, tpr, palette[direction], opacity=opacity[direction], 
							   font=args.font, path=clf_path, print_fig=False)
		precision, recall = evaluation.compute_prc(labels, pred_probs)
		evaluation.plot_curves("prc", framework, direction, recall, precision, palette[direction], opacity=opacity[direction], 
							   diag=False, font=args.font, path=clf_path, print_fig=False)
		rep_stats = evaluation.compute_eval_stats(rep_stats, framework, direction, features, labels, pred_probs, preds, 
												  splits["test"], index, n_iter=args.n_iter, interval=args.ci, 
												  metric_labels=metric_labels, path=clf_path)
		for metric in metric_labels:
			evaluation.plot_eval_metric(metric, framework, direction, rep_stats["obs"][framework][direction][metric], 
							 			rep_stats["boot"][framework][direction][metric], rep_stats["null_ci"][direction][metric], 
							 			rep_stats["fdr"][direction][metric], palette[direction], alphas=[args.alpha], 
							 			labels=axis_labels[direction], figsize=figsize[direction], ylim=ylim[metric], 
							 			dx=0.375, dxs=dxs[direction][framework], font=args.font, path=clf_path, print_fig=False)

# Compare the frameworks
print("\n------ Comparing framework prediction performance")
rep_fdr = evaluation.compare_frameworks(rep_stats, frameworks, directions, metric_labels, n_iter=args.n_iter)
for direction in directions:
	print("\n--------- {} inference".format(direction.title()))
	print("\nFDR for ROC-AUC\n{}".format(rep_fdr["rocauc"][direction]))
	evaluation.plot_framework_comparison("rocauc", direction, rep_stats["boot"], n_iter=args.n_iter, font=args.font, 
										 ylim=[0.4,0.8], yticks=np.arange(0.4,0.85,0.05), path=clf_path, print_fig=False)
	print("\nFDR for F1\n{}\n".format(rep_fdr["f1"][direction]))
	evaluation.plot_framework_comparison("f1", direction, rep_stats["boot"], n_iter=args.n_iter, font=args.font, 
										 ylim=[0.3,0.7], yticks=np.arange(0.3,0.75,0.05), path=clf_path, print_fig=False)

print("\n------ Mapping differences in forward inference")
dif_thres = evaluation.map_framework_comparison(rep_stats, metric_labels, n_iter=args.n_iter, alpha=args.alpha)
for framework in ["rdoc", "dsm"]:
	for metric in ["rocauc", "f1"]:
		utilities.map_plane(dif_thres[framework][metric], atlas, "{}figures".format(clf_path), 
							cmaps=["RdBu_r"], plane="ortho", cbar=True, vmaxs=[0.2], 
				  			suffix="{}_dif_{}_{}iter".format(metric, framework, args.n_iter), verbose=False, print_fig=False)


################################################
######### 4. Assess article partitions #########
################################################

# Compute MDS of article distances
print("\n--- ASSESSING ARTICLE PARTITIONS")

# Paths to intermediary files
mds_path = "mds/"
mod_path = "modularity/"
gen_path = "prototype/"

# Initialize the dictionary for statistics
stats_keys = ["obs", "mean", "boot", "null", "null_comparison", "df_null_interleaved"]
mod_stats = {stat: {} for stat in stats_keys} 
gen_stats = {stat: {} for stat in stats_keys}

# Parameters for multidimensional scaling (MDS)
metric = True
eps = 0.001
max_iter = 5000

# Load the MDS of article distances that was precomputed on Sherlock
mds_file = "{}data/mds_metric{}_eps{}_iter{}.csv".format(mds_path, int(metric), eps, max_iter)
X = pd.read_csv(mds_file, index_col=0, header=0).values

# Domain partitions will be assigned within discovery and replication splits
part_splits = {"discovery": splits["train"], "replication": splits["validation"] + splits["test"]}

for framework in frameworks:
	
	print("\n------ Processing the {} framework".format(titles[framework]))
	

	# Load framework data
	lists, circuits = utilities.load_framework(framework, clf=clfs[framework], suffix=suffixes[framework], path=ontol_path)
	words = sorted(list(set(lists["TOKEN"])))
	domains = style.order[framework]

	# Combine word and structure occurrences across articles
	docs = partition.load_docs(dtm, act, words)

	# Compute "prototypes" of included words and structures
	prototypes = partition.load_prototypes(lists, circuits, domains, words)

	# Partition articles by similarity to domain prototypes
	doc2dom, dom2docs = partition.load_partition(framework, clfs[framework], part_splits, prototypes, docs)

	# Initialize dictionaries for statistics
	for stat in stats_keys:
		mod_stats[stat][framework] = {}
		gen_stats[stat][framework] = {}

	for split, split_pmids in part_splits.items():

		# Load marker shapes and colors corresponding to domains
		markers, colors = [], []
		for pmid in pmids:
			idx = domains.index(doc2dom[pmid])
			markers.append(style.shapes[idx])
			if pmid in part_splits[split]:
				colors.append(style.palettes[framework][idx])
			else:
				colors.append("none")

		# Plot MDS of articles with color/shape assigned by domain partition
		print("\n--------- Plotting MDS for the {} split".format(split))
		mds.plot_mds(X, "data-driven", split, colors, markers, metric, eps, max_iter, 
					 path=mds_path, suffix=clfs[framework], print_fig=False)


################################################
### 5. Assess modularity & generalizability ####
################################################

		print("\n--------- Loading modularity and generalizability for {} set".format(split))

		# Load modularity (i.e., distance between vs. within domains)
		mod_stats = utilities.load_partition_stats(mod_stats, "mod", framework, split, lists, dom2docs, 
												   clf=clfs[framework], n_iter=args.n_iter, alpha=args.alpha, path=mod_path)
		
		# Load generalizability (i.e., similarity to domain prototypes)
		gen_stats = utilities.load_partition_stats(gen_stats, "proto", framework, split, lists, dom2docs, 
												   clf=clfs[framework], n_iter=args.n_iter, alpha=args.alpha, path=gen_path)


	print("\n--------- Plotting modularity and generalizabiltiy")

	# Plot observed modularity and null distributions by domain and split
	mod_stats["obs"][framework] = pd.read_csv("{}data/mod_obs_{}{}.csv".format(mod_path, framework, clfs[framework]), 
											  index_col=0, header=0) 
	mod_stats["df_null_interleaved"][framework] = utilities.interleave_null(mod_stats["null"][framework])
	utilities.plot_split_violins(framework, domains, mod_stats["obs"][framework], mod_stats["df_null_interleaved"][framework], 
								 mod_stats["null_comparison"][framework], style.palettes[framework], metric="mod", 
								 suffix=clfs[framework], path=mod_path, dx=style.mod_dx[framework + clfs[framework]], font=args.font,
								 ylim=[0.75,1.75], yticks=[0.75,1,1.25,1.5,1.75], interval=0.999, alphas=[0], print_fig=False)
	
	# Plot observed generalizability and null distributions by domain and split
	gen_stats["obs"][framework] = pd.read_csv("{}data/proto_obs_{}{}.csv".format(gen_path, framework, clfs[framework]), 
											  index_col=0, header=0) 
	gen_stats["df_null_interleaved"][framework] = utilities.interleave_null(gen_stats["null"][framework])
	utilities.plot_split_violins(framework, domains, gen_stats["obs"][framework], gen_stats["df_null_interleaved"][framework], 
								 gen_stats["null_comparison"][framework], style.palettes[framework], metric="gen", 
								 suffix=clfs[framework], path=gen_path, dx=style.gen_dx[framework + clfs[framework]], font=args.font,
								 ylim=[-0.25,1], yticks=[-0.25,0,0.25,0.5,0.75,1], interval=0.999, alphas=[0], print_fig=False)

	

for split in part_splits:

	print("\n------ Comparing frameworks in {} set".format(split))

	# Compare macro-averaged statistics across frameworks
	mod_fdr = utilities.compare_split_bootstraps(mod_stats, frameworks, split, n_iter=args.n_iter)
	print("\n--------- FDR for modularity\n{}".format(mod_fdr))
	mod_split_mean, mod_split_null, mod_split_boot = utilities.sort_partition_stats(mod_stats, split)
	utilities.plot_framework_comparison(mod_split_boot, mod_stats["obs"], mod_split_mean, metric="mod", 
										n_iter=args.n_iter, ylim=[1,1.25], yticks=np.arange(1.0,1.375,0.125), 
										font=args.font, path=mod_path, suffix=args.clf + "_" + split, print_fig=False)

	# Compare macro-averaged generalizability across frameworks
	gen_fdr = utilities.compare_split_bootstraps(gen_stats, frameworks, split, n_iter=args.n_iter)
	print("\n--------- FDR for generalizability\n{}\n".format(gen_fdr))
	gen_split_mean, gen_split_null, gen_split_boot = utilities.sort_partition_stats(gen_stats, split)
	utilities.plot_framework_comparison(gen_split_boot, gen_stats["obs"], gen_split_mean, metric="proto", 
										n_iter=args.n_iter, ylim=[-0.25,0.75], yticks=np.arange(-0.25,1.0,0.25), 
										font=args.font, path=gen_path, suffix=args.clf + "_" + split, print_fig=False)

