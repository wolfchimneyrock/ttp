"""charSimLevenshtein_minimal.py: Test free version of a modified Levenshtein distance that takes visual similarity into account"""

__author__      = "Vee Kaushik"

traceLeven = 0

import sys
if sys.version_info >= (3, 0):
    ranger = range
else:
    ranger = xrange

scsimtab = {
    ('0', 'O'): .9,
    ('0', 'Q'): .7,  # added becayse LPR confused ALF63Q with ALF630  
    ('1', '7'): .5, # for European 1s
    ('1', 'I'): 1,  # in some fonts ## modified from ('1', 'i'):  0.9
    ('1', 'L'): 0.8, #more similar when lower case, but LPNs areall upper case
    ('2', 'Z'): .2,
    ('3', 'E'): .1, # maybe?
    ('4', 'A'): .1, # in some fonts
    ('4', 'H'): .1, # in some fonts
    ('4', '9'): .2, # in some fonts
    ('5', '8'): .2, # confused BCV905 with BCV908 and BCV90S
    ('5', 'S'): .2,    
    ('6', 'b'): .3,
    ('8', 'B'): .3,
    ('8', 'S'): .3,    
    ('9', 'P'): .1, # maybe?
    ('A', 'H'): .2, #modified from 0.1
    ('B', 'D'): .1, 
    ('B', 'E'): .1,
    ('B', 'P'): .2,
    ('B', 'R'): .2,
    ('C', 'O'): .3,
    ('C', '0'): .2, 
    ('C', 'G'): .3, #modified from 0.2
    ('C', 'L'): .2, # added because LPR confused CSA95Y with LSA95Y  
    ('D', 'O'): .2, 
    ('E', 'F'): .2,
    ('F', 'P'): .1,
    ('F', 'R'): .1, # added because LPR confused NBS95F and NBS95R
    ('G', 'O'): .1,
    ('G', '0'): .1,
    ('G', 'Q'): .1,
    ('H', 'K'): .2, # especially in square fonts. do vehicles use these?
    ('H', 'N'): .2,
    ('I', 'L'): 0.8,
    ('I', 'T'): 0.8, # added because LPR confused CET49R with CEI49R
    ('K', 'X'): .2,
    ('M', 'N'): .1, # proportional fonts
    ('O', 'Q'): .4,
    ('P', 'R'): .2,
    ('T', 'Y'): .2, #confused CTV85Y wirh CYV85Y    
    # TO TEST SELF-TEST
    #('y', 'x'):    .1,
    ('x', 'y'): .1
}

def characterSimilarity(ch1, ch2):
    """Rate the similarity of two characters."""

    # both parameters must be single characters
    assert(len(ch1) == 1)
    assert(len(ch2) == 1)

    # Characters must be upper case
    if ch1.isalpha() & ch2.isalpha():
       assert(ch1.isupper())
       assert(ch2.isupper())

    # look up character pair in table
    if (ch1, ch2) in scsimtab:
        similarity = scsimtab[(ch1, ch2)]
    elif (ch2, ch1) in scsimtab:
        similarity = scsimtab[(ch2, ch1)]
    else:
	# character pair not in table, use default
        if ch1 == ch2:
           similarity = 1
        else:
            similarity = 0

    return similarity

def charSimLevenshtein(s, t):
    """Find the Levenshtein (edit) distance between strings."""
    effInfinity = 9999999 # effectively infinity
    
    def updateCost(baseCost, oprCost, lowestCostSoFar, operation):
        (baseCostX, baseCostY) = baseCost
        if baseCostX >= 0 and baseCostY >= 0:
            newCost = d[baseCostX][baseCostY] + oprCost
            if newCost < lowestCostSoFar:
                if traceLeven: print (newCost, oprCost, operation)
                return newCost
        return lowestCostSoFar

    # TO TEST SELF-TEST
    # make sure symmetry self-test works
    # s = s+'s'
    len_s = len(s)
    len_t = len(t)

    # CAUTION: HARDCODED INSERTION COST FOR EACH LOCATION
    d = [range(len_t+1)]
    d += [[i] for i in range(1, len_s+1)]
    if traceLeven: print (s, t, d) # diagnostic
    for i in ranger(0, len_s):
        for j in ranger(0, len_t):
            minCost = effInfinity
            
            # "delete" or "insert" is in terms of changing s into t

            # delete
            minCost = updateCost((i, j+1), 1, minCost, 'd '+s[i])
                
            # insert
            minCost = updateCost((i+1, j), 1, minCost, 'i '+t[j])

            # substite s[i] by t[j] - 0 cost if identical
            #
            # HOW CHARACTER VISUAL SIMILARITY IS TAKEN INTO ACCOUNT
            #
            # The substitution of a character that is visually similar to another character
            # is a special case of the general case of substitution.
            # Thus we modify the maximum possible substitution cost of 1 and 
            # reduce it when the characters in question are visually similar.
            # If the characters in question are say I and 1, then they appear identical in 
            # some fonts and have a character similarity of 1. then subsCost =1-1=0
            # In the next step, this low subsCost replaces minCost obtained 
            # from the insert and delete evaluations. 
            # OTOH, if the characters are not visually similar subsCost
            # will remain close to 1 and will not oust the lower cost 
            # of a delete or insert from its min status
            
            subsCost = 1 - characterSimilarity(s[i], t[j])
            
            minCost = updateCost((i, j), subsCost, minCost,'s '+s[i]+'->'+t[j])
           
            d[i+1].append(minCost)
            if traceLeven: print (d) #diagnostic
    if traceLeven: print (d) #diagnostic
    return d[len_s][len_t]
