# -*- coding: utf-8 -*-

""" creat French object pp agreement test set and collect relevant statistics """

import depTree
import json
import argparse
import pandas as pd
from collections import Counter,defaultdict
from agreement_utils import match_obj_pp_agreement,ltm_to_word,get_alt_form,read_paradigms, load_vocab, vocab_freqs

def inside(tree, a):
    # return tuple (nodes, l, r), nodes is the context, l is the cue and r is the target
    if a.child.index < a.head.index:
        nodes = tree.nodes[a.child.index: a.head.index - 1]
        l = a.child
        r = a.head
    else:
        nodes = tree.nodes[a.head.index: a.child.index - 1]
        l = a.head
        r = a.child
    return nodes, l, r

def inverted_subject(t,r,constr):
    subj_o = [n for n in t.nodes if n.head_id == r.index and n.dep_label == "nsubj"]
    if subj_o and len(subj_o) == 1:
        if subj_o[0].index > r.index:
            inverted_subj = True
        else:
            inverted_subj = False
    else:
        inverted_subj = "_"
        print("# no embedded subj issue: \n", constr)
    return inverted_subj

def plurality(morph):
    if "Number=Plur" in morph:
        return "plur"
    elif "Number=Sing" in morph:
        return "sing"
    else:
        return "none"

def extract_sent_features(t,nodes,l,r,vocab):
    """ Extracting some features of the construction and the sentence for data analysis """
    r_idx = int(r.index)
    l_idx = int(l.index)
    # problem of numbers : '3 500' is one node in conll, but two tokens for lm
    prefix = " ".join(n.word.replace(' ','') for n in t.nodes[:r_idx-1])
    prefix_lm_list = prefix.split()
    len_prefix = len(prefix_lm_list)
    n_unk = len([w for w in prefix_lm_list if w not in vocab])
    correct_number = plurality(r.morph)
    #compute the cls noun number
    context_noun_num = [plurality(n.morph) for n in nodes if
                        n.pos in ["NOUN", "PROPN"] and plurality(n.morph) != "none"]
    cls_noun_num = context_noun_num[-1] if context_noun_num else "none"

    # compute the number of attrs
    attrs = [nb for nb in context_noun_num if nb!=correct_number] if context_noun_num else [ ]

    #compute the cls number on the left of target verb
    context_num = [plurality(n.morph) for n in nodes if plurality(n.morph) != "none"]
    cls_token_num = context_num[-1] if context_num else "none"

    # calculate the major number before the target verb in the sentence
    prefix_number_values = [plurality(n.morph) for n in t.nodes[:r.index-1]]
    prefix_number = [v for v in prefix_number_values if v!="none"]
    prefix_number.reverse()# if #sing == #plur, take the closer number to target verb
    com_num = Counter(prefix_number).most_common(1)[0][0]

    # compute the first noun number
    noun_nodes = [n for n in t.nodes[:l.index-1] if n.pos in ["NOUN","PROPN"]]
    noun_num = [plurality(n.morph) for n in noun_nodes if plurality(n.morph) != "none"]
    fst_noun_num = noun_num[0] if noun_num else "none"

    # get the left closest noun of the left closet 'que' to target verbe
    que_list = [n for n in t.nodes[:r.index-1] if n.word in ["que","qu'"]]
    closest_que_id = que_list[-1].index
    que_nouns_num = [plurality(n.morph) for n in t.nodes[:closest_que_id-1] if
                        n.pos in ["NOUN", "PROPN"] and plurality(n.morph) != "none"]
    que_n_num = que_nouns_num[-1]

    len_context = r_idx - l_idx
    return correct_number,cls_noun_num,cls_token_num,fst_noun_num,com_num,que_n_num,len(attrs),prefix,len_prefix,len_context,n_unk

def collect_agreement(trees,feature_list,paradigms,vocab):
    output=[]
    whole_constr=set()
    constr_id = 0
    #t_id = 0
    #valid_t_id = []
    poses = []
    ltm_paradigms = ltm_to_word(paradigms)  # best_paradigms_lemmas['be']['Aux'][morph]=='is'

    for tree in trees :
        for a in tree.arcs :
            if a.dep_label == "acl:relcl" and a.head.pos == "NOUN" and a.child.pos == "VERB" \
                    and "Number" in a.head.morph and "Number" in a.child.morph:
                context_nodes = tree.nodes[a.head.index: a.child.index - 1]
                l = a.head
                r = a.child
                # make sure there is no "conjunction nominal subject"
                conj_pos = [n.pos for n in context_nodes if n.head_id == l.index and n.dep_label == "conj"]
                if "NOUN" in conj_pos or "PROPN" in conj_pos :
                    continue


                r_alt = get_alt_form(r.lemma, r.pos, r.morph, ltm_paradigms)
                l_alt = get_alt_form(l.lemma, l.pos, l.morph, ltm_paradigms)

                # auxiliary is "avoir", "que" is 'obj'
                r_child = [n for n in context_nodes if n.head_id == r.index]
                if not r_child:
                    continue
                pron_object = [n for n in r_child if
                               n.dep_label == "obj" and n.word in ["que", "qu'"]]  # "Rel" in n.morph]
                r_child_lemma = [n.lemma for n in r_child]
                if not pron_object or "avoir" not in r_child_lemma:
                    continue
                if len(pron_object) > 1:
                    # e.g. Entre les machines que(1) la sensibilité, que(2) l'imagination a créées ...
                    print("\n".join(str(n) for n in [l]+context_nodes+[r])+"\n")
                que_id = pron_object[0].index - 1 #python id

                if match_obj_pp_agreement(context_nodes, l, r, l_alt, r_alt, vocab):
                    pattern = "obj_aux_PP"
                    constr = " ".join(str(n.word) for n in tree.nodes[l.index - 1:r.index])
                    if constr in whole_constr:
                        continue
                    else:
                        whole_constr.add(constr)
                        print(constr_id, constr)
                        #valid_t_id.append(t_id)
                        pos = [n.pos for n in tree.nodes]
                    inverted_subj = inverted_subject(tree,r,constr)
                    correct_number, cls_noun_num, cls_token_num, fst_noun_num, com_num,que_n_num, n_attrs, prefix, len_prefix, len_context, n_unk = extract_sent_features(
                        tree, context_nodes, l, r, vocab)

                    sent = " ".join(n.word.replace(' ','') for n in tree.nodes)
                    form = r.word
                    form_alt = r_alt
                    new_sent_alt = " ".join([n.word.replace(' ','') if n.index != r.index else form_alt for n in tree.nodes])


                    output.append((pattern, constr_id, "correct", form, correct_number, cls_noun_num, cls_token_num, fst_noun_num,
                                   com_num,que_n_num,que_id, n_attrs, prefix, len_prefix, len_context, n_unk, inverted_subj, sent + " <eos>"))
                    # we don't analyse the sentences features of wrong examples, only the columns form_alt and new_sent_alt are useful
                    output.append((pattern, constr_id, "wrong", form_alt, correct_number, cls_noun_num, cls_token_num,
                                   fst_noun_num, com_num, que_n_num,que_id, n_attrs, prefix, len_prefix, len_context, n_unk, inverted_subj,
                                   new_sent_alt + " <eos>"))
                    poses.append(pos)
                    constr_id += 1
        #t_id += 1
    return output,poses#,valid_t_id

def main():
    parser = argparse.ArgumentParser(description='Generating sentences based on patterns')

    parser.add_argument('--treebank', type=str, required=True, help='input file (in a CONLL column format)')
    parser.add_argument('--paradigms', type=str, required=True,
                        help="the dictionary of tokens and their morphological annotations")
    parser.add_argument('--vocab', type=str, required=True, help='(LM) Vocabulary to generate words from')
    parser.add_argument('--lm_data', type=str, required=False, help="path to LM data to estimate word frequencies")
    parser.add_argument('--output', type=str, required=True, help="prefix for generated text and annotation data")

    args = parser.parse_args()

    print("* Loading trees")
    # trees is a list of DependencyTree objets
    trees = depTree.load_trees_from_conll(args.treebank)
    print("# {0} parsed trees loaded".format(len(trees)))
    # needed for original UD treebanks (e.g. French) which contain spans, e.g. 10-11
    # annotating mutlimorphemic words as several nodes in the tree
    #for t in trees:
    #    t.remerge_segmented_morphemes()

    paradigms = read_paradigms(args.paradigms) #d["is"] == ('be','AUX','Number=Sing|Mood=Ind|Tense=Pres|VerbForm=Fin',100)
    #print(paradigms["fait"])
    vocab = load_vocab(args.vocab)

    data,poses  = collect_agreement(trees, ["Number"], paradigms, vocab) #,trees_id
    print("# In total, {0} agreement sentences collected".format(int(len(data) / 2)))


    data = pd.DataFrame(data, columns=["pattern","constr_id", "class", "form", "correct_number","cls_noun_num",
                                   "cls_token_num", "fst_noun_num","com_num", "que_n_num", "que_id", "n_attrs", "prefix","len_prefix", "len_context", "n_unk","inverted_subj","sent"])

    if args.lm_data:
        freq_dict = vocab_freqs(args.lm_data + "/train.txt", vocab)
        data["freq"] = data["form"].map(freq_dict)
        fields = ["pattern","constr_id", "class", "form", "correct_number","cls_noun_num", "cls_token_num",
                  "fst_noun_num", "com_num","que_n_num", "que_id","n_attrs", "freq", "prefix","len_prefix", "len_context", "n_unk","inverted_subj","sent"]
    else:
        fields = ["pattern","constr_id", "class", "form", "correct_number", "cls_noun_num", "cls_token_num",
                  "fst_noun_num", "com_num","que_n_num", "que_id","n_attrs", "freq", "prefix","len_prefix", "len_context", "n_unk","inverted_subj", "sent"]

    data[fields].to_csv(args.output  + ".tab", sep="\t", index=False)
    with open(args.output + ".txt","w") as txt:
        txt.write("\n".join(data['sent'].tolist()))

    # save the valid sentence ids of the raw gutenberg copurs
    #with open(args.output + "_trees_id.json", 'w') as f:
    #    json.dump(trees_id, f)

    """
    # collect and save the sequence of PoS tags of every sentence
    d = defaultdict(int)
    for sent in poses:
        for pos in sent:
            if pos in d:
                d[pos] += 1
            else:
                d[pos] = 1
    print(len(d.keys()))
    print(d)

    with open(args.output + "_pos-tags.json", 'w') as f:
        json.dump(poses, f)
    """

if __name__ == "__main__":
    main()


