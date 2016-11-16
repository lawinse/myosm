# -*- coding:utf-8 -*- 
from sklearn.externals import joblib

def getEditDistance(word1,word2):
    l1, l2 = len(word1)+1, len(word2)+1
    dp = [[0 for _ in xrange(l2)] for _ in xrange(l1)]
    for i in xrange(l1):
        dp[i][0] = i
    for j in xrange(l2):
        dp[0][j] = j
    for i in xrange(1, l1):
        for j in xrange(1, l2):
            dp[i][j] = min(dp[i-1][j]+1, dp[i][j-1]+1, dp[i-1][j-1]+1.5*(word1[i-1]!=word2[j-1]))
    return int(round(dp[-1][-1]))
class BKTree:
    def __init__(self, words,distfn=getEditDistance):
        self.distfn = distfn
        self.mark_removed = 0;
        self.dic = words[:]
        it = iter(words)
        root = it.next()
        self.tree = (root, {})

        for i in it:
            self._add_word(self.tree, i)

    def _rebuild(self, new_words):
        self.mark_removed = 0;
        self.dic = new_words[:]
        it = iter(new_words)
        root = it.next()
        self.tree = (root, {})

        for i in it:
            self._add_word(self.tree, i)

    def _add_word(self, parent, word):
        if (parent == None): # root
            self.tree = (word, {});
            return;
        p = parent;
        while 1:
            pword, children = p
            d = self.distfn(word, pword)
            if d == 0 and children.has_key("mark_removed"): 
                children.pop("mark_removed");
                self.mark_removed -= 1;
                break;
            elif children.has_key(d):
                p = children[d];
            else:
                children[d] = (word, {});
                break;

    def _remove_word(self, parent, word):
        p = parent;
        while 1:
            pword,children = p;
            if (pword == word):
                children['mark_removed'] = -1;
                self.mark_removed += 1;
                break;
            else:
                edis = self.distfn(word,pword);
                child = children.get(edis);
                if child == None: break;
                p = child;

    def alter(self, new_words):
        if not hasattr(self,'mark_removed'): self.mark_removed = 0;
        if (self.mark_removed > len(self.dic)/3):
            self._rebuild(new_words);
            return;

        need_to_added = set(new_words)-set(self.dic);
        need_to_removed = set(self.dic)-set(new_words);
        if len(need_to_added) > 0:
            for i in iter(need_to_added):
                self._add_word(self.tree,i);

        if len(need_to_removed) > 0:
            for i in iter(need_to_removed):
                self._remove_word(self.tree,i);

        self.dic = new_words[:]

    def query(self, word, n):
        def rec(parent):
            pword, children = parent
            d = self.distfn(word, pword)
            results = []
            if d <= n:
                if not children.has_key('mark_removed'):
                    results.append((d, pword)) 
                
            for i in range(d-n, d+n+1):
                child = children.get(i)
                if child is not None:
                    results.extend(rec(child))
            return results
        def cmp(x,y):
            if (x[0] == y[0]):  
                return len(y[1])-len(x[1])
            else:
                return x[0]-y[0]

        # sort by distance
        return sorted(rec(self.tree),cmp)




if __name__ == "__main__":

    tree = BKTree(
                  ["apple","applela","pinapple","ahhle","pear"])
    print tree.query("apple", 3)


