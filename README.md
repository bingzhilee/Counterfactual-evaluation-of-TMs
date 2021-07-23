# Assess syntactic ability of Transformer LM via counterfactual evaluation
This repository contains data and code for a counterfactual evaluation of Transformer LM on French object past participle agreement

#### Creating evaluation datasets

`data/treebanks` contains ud treebanks of sentences containing target agreement and conllu format [Gutenberg](https://gitlab.huma-num.fr/bli/syntactic-ability-nlm/-/blob/master/data/treebank/French/gutenberg-treebank.conllu) treebank.

`data/agreement`contains sentences used in agreement task, the basic features and the prediction of the pretrained Transformer model(the best perplexity score: 28.2)

`src/creat_testset` contains the scripts used to extract valid sentences and basic features from `*.conllu` file

### Training data based on Wikipedia

Each corpus consists of around 100M tokens, we used training (80M) and validation (10M) subsets in our experiments. All corpora were shuffled at sentence level.

Each vocabulary lists words according to their indices starting from 0, `<unk>`,`<bos>` and `<eos>` tokens are already in the vocabulary. 

- French [train]() / [valid]() / [test]() / [vocab]()


