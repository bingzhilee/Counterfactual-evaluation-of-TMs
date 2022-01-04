# Intership of Camille LE (summer 2020): Assess syntactic ability of Transformer LM via counterfactual evaluation
This repository contains data and code for a counterfactual evaluation of Transformer LM on French object past participle agreement

### Creating object past-participle agreement datasets

`data/treebanks` contains ud treebank(102 sentences)  and [Gutenberg](https://gitlab.huma-num.fr/bli/syntactic-ability-nlm/-/blob/master/data/treebank/French/gutenberg-treebank.conllu) treebank.

`data/agreement`contains sentences used in agreement task, the basic features and the prediction of the pretrained Transformer model(the best one with perplexity 28.2)

`src/creat_testset` contains the scripts used to extract valid sentences and basic features from `*.conllu` file

### Creating counterfactual evaluation datasets





