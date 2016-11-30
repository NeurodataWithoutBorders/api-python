
# function get_possible_matches - used to return list of possible
# matching words in a list if the word was supposed to be in the
# list but not found, possibly due to a spelling error.
# adapted from:
# http://norvig.com/spell-correct.html


alphabet = 'abcdefghijklmnopqrstuvwxyz'

def edits1(word):
   splits     = [(word[:i], word[i:]) for i in range(len(word) + 1)]
   deletes    = [a + b[1:] for a, b in splits if b]
   transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b)>1]
   replaces   = [a + c + b[1:] for a, b in splits for c in alphabet if b]
   inserts    = [a + c + b     for a, b in splits for c in alphabet]
   return set(deletes + transposes + replaces + inserts)

def known_edits2(word, choices):
    return set(e2 for e1 in edits1(word) for e2 in edits1(e1) if e2 in choices)

def known(words, choices): return set(w for w in words if w in choices)


def get_possible_matches(word, choices):
    """ given word, that is not in list words, find possible matches based on
    edits.  This used to generate list of possible matches in case there was a
    misspelling"""
    ch = set(choices)
    candidates = known(edits1(word), ch) or known_edits2(word, ch)
    return sorted(list(candidates))
    

def test_get_possible_matches():
    choices = ["stimulus", "hippocampus", "mouse", "module", "interface"]
    words = ["stimuls", "hipppocampus", "mose", "modlue", "interfaces"]
    for word in words:
        possible_matches = get_possible_matches(word, choices)
        print ("%s found %s" % (word, possible_matches))


if __name__ == '__main__':
    test_get_possible_matches()
