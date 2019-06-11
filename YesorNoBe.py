import re

import requests
import spacy

nlp = spacy.load("en_core_web_sm")

url_1 = "https://www.wikidata.org/w/api.php"
url_2 = "https://query.wikidata.org/sparql"

# Parameters for entity and property searching respectively
params_prop = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json', 'type': 'property'}
params_en = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}

# Pre-defined property Dictionary
prop_dict = {
    "member": "has part",
    "real name": "birth name",
    "child": "children"
}


# query with wikidata
def query(prop, entity):
    query = '''
        SELECT ?NameLabel WHERE{
            wd:%s wdt:%s ?Name .
            SERVICE wikibase:label { bd:serviceParam wikibase:language "en".}
    }''' % (entity, prop)
    data = requests.get(url_2, params={'query': query, 'format': 'json'}).json()
    return data


def create_and_fire_queryYesorNoBe(line):
    parse = nlp(line)
    subj = []
    obj = []
    answer1 = []
    answer2 = []
    labeled = []
    conj = []
    result = []
    allanswer1 = ""
    allanswer2 = ""
    allsub = ""
    allobj = ""
    cc = 0
    onlyflag = 0
    personflag = 0
    orgflag = 0
    type1 = 0  # Dependency Method: Yes/No question for " Is X Y of Z ? "
    type2 = 0  # Dependency Method: Yes/No question for " Is X Y ? " In most of cases, it asked occupation ???
    type3 = 0  # Regular expression Method: when type 1 and type 2 failed

    # Name entities searching
    for ent in parse.ents:
        if (ent.label_ != []):
            labeled.append(ent.lemma_)
            if (ent.label_ == "PERSON"):
                personflag = 1
            if (ent.label_ == "ORG"):
                orgflag = 1

    # Type matching
    for token in parse:
        if token.dep_ == "attr":
            type2 = 1
        if (token.dep_ == "prep") and (token.lemma_ == "of"):
            type1 = 1
            type2 = 0
    if (type1 == 0) and (type2 == 0):
        type3 = 1

    # Yes/No question for " Is X Y of Z ? "
    if (type1 == 1):
        for token in parse:
            # print("\t".join((token.text, token.dep_)))
            if token.dep_ == "cc" and token.lemma_ == "and":
                cc = cc + 1
                conj.append(token.lemma_)
            if token.lemma_ == "be" and token.dep_ == "ROOT":
                for t in token.subtree:
                    if t.dep_ == "nsubj" or t.dep_ == "acomp":
                        answer1.append(t.lemma_)
                    if t.dep_ == "compound" and t.head.dep_ == "nsubj":
                        answer1.append(t.lemma_)
                    if t.dep_ == "conj":
                        answer2.append(t.lemma_)
                    if t.dep_ == "compound" and t.head.dep_ == "conj":
                        answer2.append(t.lemma_)
        allanswer1 = (" ".join(answer1))
        line = line.replace(allanswer1, '')

        if (cc != 0):
            allconj = (" ".join(conj))
            allanswer2 = (" ".join(answer2))
            line = line.replace(allconj, '')
            line = line.replace(allanswer2, '')

        parse = nlp(line)
        for token in parse:
            multi_of1 = 0
            multi_of2 = 0
            if token.dep_ == "nsubj" or token.dep_ == "attr":
                for t in token.subtree:
                    if t.dep_ == "prep":
                        multi_of1 = multi_of1 + 1
                        multi_of2 = multi_of2 + 1
                for t1 in token.subtree:
                    if t1.dep_ == "prep":
                        multi_of1 = multi_of1 - 1
                    if multi_of1 == 0:
                        break
                    if t1.lemma_ != "who" and t1.lemma_ != "what":
                        if (t1.lemma_ != "the" and t1.lemma_ != "a" and t1.lemma_ != "an"):
                            subj.append(t1.lemma_)
                for t2 in token.subtree:
                    if t2.dep_ == "prep":
                        multi_of2 = multi_of2 - 1
                    if multi_of2 == 0:
                        if t2.dep_ == "pobj":
                            obj.append(t2.lemma_)
                        if t2.dep_ == "compound" and t2.head.dep_ == "pobj":
                            obj.append(t2.lemma_)

        allsub = (" ".join(subj))
        allobj = (" ".join(obj))

        if ("only" in allsub):
            onlyflag = 1
            allsub = allsub.replace("only", '')
            allsub = allsub.lstrip()

        for en in labeled:
            if en in allsub:
                allsub = en
            if en in allobj:
                allobj = en
            if en in allanswer1:
                allanswer1 = en
            if (allanswer2 != []):
                if en in allanswer2:
                    allanswer2 = en

        if allsub in prop_dict:
            allsub = prop_dict[allsub]

    # Yes/No question for " Is X Y ? "
    if (type2 == 1):
        for token in parse:
            # print("\t".join((token.text, token.dep_)))
            if token.lemma_ == "be" and token.dep_ == "ROOT":
                for t1 in token.subtree:
                    if t1.dep_ == "nsubj" or t1.dep_ == "acomp":
                        obj.append(t1.lemma_)
                    if t1.dep_ == "compound" and t1.head.dep_ == "nsubj":
                        obj.append(t1.lemma_)
                for t2 in token.subtree:
                    if t2.dep_ == "advmod" or t2.dep_ == "attr":
                        answer1.append(t2.lemma_)
                    if t2.dep_ == "compound" and (t2.head.dep_ == "attr" or t2.head.dep_ == "advmod"):
                        answer1.append(t2.lemma_)

        allanswer1 = (" ".join(answer1))
        allobj = (" ".join(obj))

        if ("only" in allanswer1):
            onlyflag = 1
            allanswer1 = allanswer1.replace("only", '')
            allanswer1 = allanswer1.lstrip()

        for en in labeled:
            if en in allsub:
                allsub = en
            if en in allobj:
                allobj = en
            if en in allanswer1:
                allanswer1 = en
            if (answer2 != []):
                if en in allanswer2:
                    allanswer2 = en

        if allsub in prop_dict:
            allsub = prop_dict[allsub]

        if not allsub:
            if (personflag == 1):
                allsub = "occupation"
            if (orgflag == 1):
                allsub = "instance of"

        # Guess step
        if (personflag == 0 and orgflag == 0):
            allsub = "occupation"

    # Regular expression method
    if (type3 == 1):
        s = re.sub('[?]', '', line)
        m = re.search('(Is|Are)(.*)(a|the)(.*)', s)
        if not m:
            print("\t", "Yes")
            return
        allobj = (m.group(2))
        allanswer1 = (m.group(4))

        if ("only" in allobj):
            onlyflag = 1
            allobj = allobj.replace("only", '')
            allobj = allobj.lstrip()

        for en in labeled:
            if en in allsub:
                allsub = en
            if en in allobj:
                allobj = en
            if en in allanswer1:
                allanswer1 = en
            if (answer2 != []):
                if en in allanswer2:
                    allanswer2 = en

        if allsub in prop_dict:
            allsub = prop_dict[allsub]

        if not allsub:
            if (personflag == 1):
                allsub = "occupation"
            if (orgflag == 1):
                allsub = "instance of"

        # Guess step
        if (personflag == 0 and orgflag == 0):
            allsub = "occupation"

    if (allsub == "") or (allobj == "") or (allanswer1 == ""):
        # Random Guess
        print("\t", "Yes")
        return 1

    params_prop['search'] = allsub
    result_pro = []
    json1 = requests.get(url_1, params_prop).json()

    params_en['search'] = allobj
    result_en = []
    json2 = requests.get(url_1, params_en).json()

    # Store the returning ID
    for p in json1['search']:
        result_pro.append(p['id'])
    for e in json2['search']:
        result_en.append(e['id'])

    # Print available answers
    findflag = 0
    for X in result_pro:
        if findflag == 0:
            for Y in result_en:
                data = query(X, Y)
                if (data['results']['bindings'] != []):
                    for item in data['results']['bindings']:
                        for var in item:
                            result.append("{}".format(item[var]['value']))
                    findflag = 1

    if allanswer1 in result:
        if (cc == 0) and onlyflag == 0:
            print("\t", "Yes")
            return 1
        if (cc == 1) and onlyflag == 0:
            if allanswer2 in result:
                print("\t", "Yes")
                return 1
        if (cc == 0) and onlyflag == 1:
            new_result = (" ".join(result))
            new_result = new_result.replace(allanswer1, "")
            new_result = new_result.strip()
            if not new_result:
                print("\t", "Yes")
                return 1
        if (cc == 1) and onlyflag == 1:
            new_result = (" ".join(result))
            new_result = new_result.replace(allanswer1, "")
            new_result = new_result.replace(allanswer2, "")
            new_result = new_result.strip()
            if not new_result:
                print("\t", "Yes")
                return 1

    if findflag == 1:
        print("\t", "No")
        return 1

    if (findflag == 0):
        # No answers available : Random Guess
        print("\t", "Yes")
        return 1
