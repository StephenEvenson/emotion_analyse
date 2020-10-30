import jieba

jieba.load_userdict('./dict.txt')
jieba.suggest_freq('奥利给', True)
jieba.suggest_freq('奥利奥', True)
