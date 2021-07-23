# -*- coding: utf-8 -*-

import pandas as pd

from collections import defaultdict
import string



def read_paradigms(path):
    """ reads morphological paradigms from a file with token, lemma, tag, morph, freq fields
        returns a simple dict: token -> list of all its analyses and their frequencies """
    d = defaultdict(list)
    with open(path, "r") as f:
        for line in f:
            token, lemma, tag, morph, freq = line.split("\t")
            s_m = morph.split("|")
            s_m.sort()
            morph = "|".join(s_m)
            # Mood=Ind|Number=Sing|Tense=Pres|VerbForm=Fin --> Number=Sing|Mood=Ind|Tense=Pres|VerbForm=Fin
            d[token].append((lemma, tag, morph, int(freq)))
            # d["is"] == ('be','AUX','Number=Sing|Mood=Ind|Tense=Pres|VerbForm=Fin',100)
    return d

def load_vocab(vocab_file):
    f_vocab = open(vocab_file, "r")
    vocab = {w: i for i, w in enumerate(f_vocab.read().split())}
    f_vocab.close()
    return vocab

def vocab_freqs(train_data_file, vocab):
    train_data = open(train_data_file).readlines()
    freq_dict = {}
    for w in vocab:
        freq_dict[w] = 0
    for line in train_data:
        for w in line.split():
            if w in vocab:
                freq_dict[w] += 1
    return freq_dict

def ltm_to_word(paradigms):
    """ converts standard paradigms dict (token -> list of analyses) to a dict (l_emma, t_ag, m_orph -> word)
        (where word in the most frequent form, e.g. between capitalized and non-capitalized Fanno and fanno) """
    #paradigms = read_paradigms("/private/home/gulordava/edouard_data/itwiki//paradigms_UD.txt")

    paradigms_lemmas = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for w in paradigms:
        for lemma, tag, morph, freq in paradigms[w]:
            paradigms_lemmas[(lemma, tag)][morph][w] = int(freq)

    best_paradigms_lemmas = defaultdict(lambda: defaultdict(lambda: defaultdict(str)))
    for l, t in paradigms_lemmas:
        for m in paradigms_lemmas[(l, t)]:
            word = sorted(paradigms_lemmas[(l, t)][m].items(), key=lambda x: -x[1])[0][0]
            best_paradigms_lemmas[l][t][m] = word
    return best_paradigms_lemmas
    # "be" the best/most frequent form is "is": best_paradigms_lemmas['be']['Pos']["..."]=='is'

def features(morph, feature_list):
    '''
    :param morph: conllu features string
    :param feature_list: ex,['Number']
    :return: morph string or 'Number'
    '''
    if not feature_list:
        return morph

    all_feats = morph.split("|")
    feat_values = tuple(f for f in all_feats if f.split("=")[0] in feature_list)

    return "|".join(feat_values)

def alt_numeral_morph(morph):
    if "Number=Plur" in morph:
        morph_alt = morph.replace("Plur", "Sing")
        return "plur", morph_alt
    elif "Number=Sing" in morph:
        morph_alt = morph.replace("Sing", "Plur")
        return "sing", morph_alt

def get_alt_form(lemma, pos, morph, ltm_paradigms):
    #print(morph)
    _, alt_morph = alt_numeral_morph(morph)
    return ltm_paradigms[lemma][pos][alt_morph]


def is_vowel(c):
    return c in ["a","à","â","æ","o","ô","u","ù","û","ü","e","é","è","ê","ë","i","î","ï","A","À","Â","Æ","O","Ô","U","Û","Ü","Ù","E","I","Ï","Î","É","È","Ê","Ë"]


def match_features(w1, w2):
    #if w1 in ["est","sont","es"] or w2 in ["est","sont","êtes"]:# for subject verb auxilary agreement
    #    return True
    return w1[0].isupper() == w2[0].isupper() and is_vowel(w1[0]) == is_vowel(w2[0])

def is_good_form(gold_form, gold_morph, lemma, pos, vocab, ltm_paradigms):
    _, alt_morph = alt_numeral_morph(gold_morph)
    alt_form = ltm_paradigms[lemma][pos][alt_morph]
    # alternative form belong to paradigms and vocabulary
    if not alt_form in vocab:
        return False
    # sing and plur cue/target word shouldn't have the same word form
    if gold_form == alt_form:
        return False
    if gold_form is None:
        print(gold_form, gold_morph)
        return True
    # same case and both starts with vowel or non-vowel
    if not match_features(alt_form, gold_form):
        return False
    return True


def match_obj_pp_agreement(nodes,l,r,l_alt,r_alt,vocab):
    """
    verify if satisfy object participle verb agreement condition in French
    :param nodes: context nodes
    :param l: cue
    :param r: target
    :return: bool
    """

    l_feats = features(l.morph, ["Gender", "Number"])
    r_feats = features(r.morph, ["Gender", "Number"])

    if l_feats and r_feats and l_feats == r_feats and len(l_feats.split("|")) == 2 :
        # all the words between cue and target (included) should be in vocabulary :
        in_vocab = all([n.word in vocab for n in nodes + [l, r]])
        if not in_vocab:
            return False

        if not r_alt in vocab or not l_alt in vocab:
            return False
        # sing and plur cue/target word shouldn't have the same word form
        if r_alt == r.word or l_alt == l.word:
            return False

        return match_features(r_alt, r.word) and match_features(l_alt, l.word)

    else:
        return False