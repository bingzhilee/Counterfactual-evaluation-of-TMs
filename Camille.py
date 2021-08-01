import Tree 
import json
from itertools import combinations

#BUT : 
# - récupérer les phrases intéressantes
# - les modifier
# - tout stocker dans un fichier json


"""RECUPERATION DES PHRASES INTERESSANTES"""


def create_dict(conllu_file):
    """
    en entrée : le fichier .conllu
    en sortie : un dictionnaire de dictionnaires de dictionnaires {lemma : {pos : {feats : form}}} avec les formes fléchies
    """
    stream = open(conllu_file, encoding = "utf-8")

    dico = dict()
    
    while True:
        line = stream.readline()
        if not line:  # End of file
            break

        data = line.split("\t")
        if len(data) == 1:
            continue
        if data[0].isdigit:  #dans ud-treebank, on peut avoir des contractions 12-13 !
            form = data[1]
            lemma = data[2]
            upos = data[3]
            feats = data[5]
            
            if lemma in dico:
                if upos in dico[lemma]:
                    dico[lemma][upos][feats] = form
                else:
                    pos_dict = {feats : form}
                    dico[lemma][upos] = pos_dict
            else:
                pos_dict = {feats : form}
                lemma_dict = {upos : pos_dict}
                dico[lemma] = lemma_dict

    stream.close()

    return dico


def pluralize(node, forms_dico):
    """
    en entrée : le noeud du mot au singulier et le dictionnaire des formes fléchies
    en sortie : le mot au pluriel 
    """
    lemma = node.lemma
    upos = node.pos
    feats = node.morph.replace("Number=Sing", "Number=Plur") 

    if lemma in forms_dico:
        if upos in forms_dico[lemma]:
            if feats in forms_dico[lemma][upos]:
                return forms_dico[lemma][upos][feats]
    return ""

def interesting(tree, forms_dico):
    """
    en entrée : l'arbre d'une phrase analysée 
    en sortie : un booléen qui indique si la phrase nous intéresse 
    c'est-à-dire si les éléments du préfixe sont au singulier et pluralisables. 
    CRITERES A RAJOUTER : ----------------------------------------------------------------A AMELIORER--------------------------------------------
    - au moins un distracteur 
    """
    for node in tree.nodes:
        if node.dep_label == "acl:relcl":   #c'est la fin du préfixe
            break
        if "Number=Plur" in node.morph:  #on ne veut aucun mot pluriel dans le préfixe
            return False
        
        # ------------------------Désactivé pour le moment car ud-treebank-103 est trop petit et fait exclure tous les trees-------------------------------------------------------------------------------------
        """
        if "Number=Sing" in node.morph:  
            if pluralize(node, forms_dico)=="": #on veut que les mots singuliers soient pluralisables
                return False
        """

    return True

def interesting_trees(conllu_file, forms_dico):
    """
    en entrée : le fichier .conllu.
    en sortie : la liste des trees qui nous intéressent.
    """
    trees = Tree.load_trees_from_conll(conllu_file)

    our_trees = []
    for i in range(len(trees)):
        if interesting(trees[i], forms_dico):
            our_trees.append(trees[i])

    return our_trees



"""GENERATION DE PHRASES MODIFIEES"""

def create_sentence(words):
    """
    en entrée : une liste de mots
    en sortie : la phrase correspondante   ------------------------------------A AMELIORER ? ------------------------------------------------------
    """
    sentence = ""
    second_bracket = False

    for word in words:
        if sentence.endswith("'") or sentence.endswith("(") or sentence.endswith("[") or word in [".", ",", ")", "]"]: #apostrophe, point etc. 
            sentence += word

        #gestion des guillemets
        elif word == "\"" and second_bracket == False:
            sentence += " " + word
            second_bracket = True
        elif word == "\"" and second_bracket == True:
            sentence += word
            second_bracket = False
        elif sentence.endswith("\"") and second_bracket == True:
            sentence += word

        #gestion des tirets
        elif len(word)> 1 and word.startswith("-"):
            sentence += word

        else:
            sentence += " " + word
    
    #contractions du français ---------------------------------------------------A COMPLETER ?--------------------------------
    sentence = sentence.replace("à le", "au")
    sentence = sentence.replace("à les", "aux")
    sentence = sentence.replace("de le", "du")
    sentence = sentence.replace("de les", "des")

    return sentence

def sing_list(tree):
    """
    en entrée : l'arbre d'une phrase
    en sortie : la liste des positions des éléments du préfixe qui sont au singulier
    """
    liste = []
    for node in tree.nodes:
        if node.dep_label == "acl:relcl":   #c'est la fin du préfixe
            break
        if "Number=Sing" in node.morph:
            liste.append(node.index-1)      #on note l'index -1 pour avoir le début de la phrase à 0.
    
    return liste


def modify(trees, forms_dico):
    """
    en entrée : la liste des trees de base et le dictionnaire des formes fléchies
    en sortie : un bloc (string) avec pour chaque ligne "phrase de base (\t) phrase modifiée" 
     + (\t) type de modification -----------------------A AJOUTER-----------------------------------------------------------------------------
    """
    result = ""
    for tree in trees:
        #création de la liste des mots
        words = []
        for node in tree.nodes:
            words.append(node.word)
        
        original = create_sentence(words) #phrase de base
        sing_positions = sing_list(tree) # on récupère la position (début = 0) des mots au singulier, à pluraliser.

        bloc = ""

        for i in range(len(sing_positions)):
        #for i in range(1): #test avec juste 1 modif
            n = i+1  #le nombre de modifications à effectuer

            comb_list = combinations(sing_positions,n)
            for comb in comb_list:
                new_words = words.copy()
                #print(comb)
                for index in comb:
                    new_words[index] = pluralize(tree.nodes[index], forms_dico)
                modified = create_sentence(new_words)

                line = original + "\t" + modified
                bloc += line + "\n"
        
        result += bloc + "\n"

    return result

def generate_json(data):
    with open("modif.json", "w") as my_file:
        json.dump(data, my_file)


#------------------------------------------MISE EN OEUVRE----------------------------------------------------------------------------------------
#conll_file = "/Users/Camille/Desktop/2021-Stage-M1-LI/syntactic_ability_nlm/notebooks/test-data/gutenberg-1.conllu"
conll_file = "/Users/Camille/Desktop/2021-Stage-M1-LI/syntactic_ability_nlm/data/treebanks\\French/ud_treebank-103.conllu"

#1) Récupération des phrases intéressantes (arbres)
forms_dico = create_dict(conll_file)
trees = interesting_trees(conll_file, forms_dico) 
print(len(trees))

#2) Génération de phrases modifiées
#result = modify(trees, forms_dico)



"""    
#3) Enregistrement dans le fichier modif.json    
#generate_json(result)

with open("modif.json") as my_file:
    data = json.load(my_file)

print(data)

"""

"""
# BROUILLON - ESSAIS

print(len(trees))
deptree = trees[0]
print(deptree)
a_node = deptree.nodes[1]
print(pluralize(a_node, forms_dico))

modified = modify(trees[23])
"""


