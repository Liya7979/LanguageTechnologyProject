import spacy
import requests
import re

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
    "child": "children",
    "play": "instrument",
    "influence":"influenced by",
    "make": "genre"
}

# Pre-defined entity Dictionary
en_dict = {
    "Ludwig van": "Ludwig van Beethoven"
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


def create_and_fire_queryYesorNoDo(line):
    parse = nlp(line)
    subj = []
    obj = []
    answer1 = []
    answer2 = []
    labeled = []
    result = []
    allanswer2 = ""
    onlyflag=0
    cc=0

    # Name entities searching
    for ent in parse.ents:
        if (ent.label_ != []):
            labeled.append(ent.lemma_)
            if (ent.label_ == "PERSON"):
                personflag = 1
            if (ent.label_ == "ORG"):
                orgflag = 1

    for token in parse:
        #print("\t".join((token.text, token.dep_)))
        if(token.dep_=="ROOT"):
            subj.append(token.lemma_)
            for t in token.subtree:
                if t.dep_=="nsubj":
                    obj.append(t.lemma_)
                if t.dep_=="compound" and t.head.dep_=="nsubj":
                    obj.append(t.lemma_)
                if t.dep_=="dobj"or t.dep_=="pobj":
                    answer1.append(t.lemma_)
                if (t.dep_=="compound" or t.dep_=="amod") and (t.head.dep_=="dobj" or t.head.dep_=="pobj"):
                    answer1.append(t.lemma_)
                if(t.dep_=="cc") and (t.lemma_=="and"):
                    cc=cc+1
                if t.dep_ == "conj":
                    answer2.append(t.lemma_)
                if t.dep_ == "compound" and t.head.dep_ == "conj":
                    answer2.append(t.lemma_)

        if(token.dep_=="advmod")and(token.lemma_=="only"):
            onlyflag=1

    allsub = (" ".join(subj))
    allobj = (" ".join(obj))
    allanswer1= (" ".join(answer1))

    if (allsub=="")or(allobj=="")or(allanswer1==""):
        # Random Guess
        print("Yes")
        return

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

    if allsub == "influence":
        t = allanswer1
        allanswer1 = allobj
        allobj = t

    if allsub in prop_dict:
        allsub = prop_dict[allsub]

    if allanswer1 in en_dict:
        allanswer1 = en_dict[allanswer1]

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
            print("Yes")
            return 1
        if (cc == 1) and onlyflag == 0:
            if allanswer2 in result:
                print("Yes")
                return 1
        if (cc == 0) and onlyflag == 1:
            new_result = (" ".join(result))
            new_result = new_result.replace(allanswer1, "")
            new_result = new_result.strip()
            if not new_result:
                print("Yes")
                return 1
        if (cc == 1) and onlyflag == 1:
            new_result = (" ".join(result))
            new_result = new_result.replace(allanswer1, "")
            new_result = new_result.replace(allanswer2, "")
            new_result = new_result.strip()
            if not new_result:
                print("Yes")
                return 1

    if findflag == 1:
        print("No")
        return 1

    if (findflag == 0):
        # No answers available : Random Guess
        print("Yes")
        return 1
