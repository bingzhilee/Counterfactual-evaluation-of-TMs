# Syntactic ability of neural language models
This repository contains data and code for a reproduction of the experiments of EMNLP2021-submission (Li, Wisnewski and Crabbé).

#### Creating evaluation datasets

`data/treebank` contains conllu format treebanks 

`data/agreement`contains sentences of agreement test set used in the experiments


### Training data based on Wikipedia

Each corpus consists of around 100M tokens, we used training (80M) and validation (10M) subsets in our experiments. All corpora were shuffled at sentence level.

Each vocabulary lists words according to their indices starting from 0, `<unk>`,`<bos>` and `<eos>` tokens are already in the vocabulary. 

- French [train]() / [valid]() / [test]() / [vocab]()

- English [train](https://dl.fbaipublicfiles.com/colorless-green-rnns/training-data/English/train.txt) / [valid](https://dl.fbaipublicfiles.com/colorless-green-rnns/training-data/English/valid.txt) / [test](https://dl.fbaipublicfiles.com/colorless-green-rnns/training-data/English/test.txt) / [vocab](https://dl.fbaipublicfiles.com/colorless-green-rnns/training-data/English/vocab.txt)

