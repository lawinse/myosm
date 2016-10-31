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

        it = iter(words)
        root = it.next()
        self.tree = (root, {})

        for i in it:
            self._add_word(self.tree, i)

    def _add_word(self, parent, word):
        pword, children = parent
        d = self.distfn(word, pword)
        if d in children:
            self._add_word(children[d], word)
        else:
            children[d] = (word, {})

    def query(self, word, n):
        def rec(parent):
            pword, children = parent
            d = self.distfn(word, pword)
            results = []
            if d <= n:
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


