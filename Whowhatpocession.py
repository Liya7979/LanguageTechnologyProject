import spacy
import requests

nlp = spacy.load("en_core_web_sm")

url_1 = "https://www.wikidata.org/w/api.php"
url_2 = "https://query.wikidata.org/sparql"

# Parameters for entity and property searching respectively
params_prop = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json', 'type': 'property'}
params_en = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}

# Pre-defined Dictionary
prop_dict = {
    "band member": "has part",
    "member": "has part",
    "real name": "birth name",
    "name": "birth name",
    "where bear": "place of birth",
    "when die": "date of death",
    "where die": "place of death",
    "when bear": "date of birth",
    "child": "children"
}
# Entity Special cases
def special_checking(line,allobj):
    if "A-Ha" in line:
        allobj = "A-Ha"
    if "BTS" in line:
        allobj = "BTS"
    if "The Script" in line:
        allobj = "The Script"
    return allobj

# Negation fix
def fix_negation(string):
	if "n't" in string:
		return string.replace(" n't", "n't")
	return string

# query with wikidata
def query(prop, entity):
    query = '''
        SELECT ?NameLabel WHERE{
            wd:%s wdt:%s ?Name .
            SERVICE wikibase:label { bd:serviceParam wikibase:language "en".}
    }''' % (entity, prop)
    data = requests.get(url_2, params={'query': query, 'format': 'json'}).json()
    return data


def create_and_fire_queryWhowhatpocession(line):
    parse = nlp(line)
    subj = []
    obj = []
    labeled = []
    flag = 0
    start = 0

    for ent in parse.ents:
        if (ent.label_ != []):
            labeled.append(ent.lemma_)

    for token in parse:
        #print("\t".join((token.text, token.dep_)))
        if (token.dep_ == "poss"):
            obj.append(token.lemma_)
        if (token.dep_ == "compound" or token.dep_ == "amod") and (token.head.dep_ == "poss"):
            obj.append(token.lemma_)
        if token.dep_ == "case":
            start = 1
        if start ==1:
            if token.dep_ == "attr" or token.dep_ == "nsubj" :
                subj.append(token.lemma_)
            if (token.dep_ == "compound")and (token.head.dep_ == "attr" or token.dep_ == "nsubj"):
                subj.append(token.lemma_)

    allsub = (" ".join(subj))
    allobj = (" ".join(obj))

    # Check up with dictionary
    if allsub in prop_dict:
        allsub = prop_dict[allsub]

    # fix
    allobj = special_checking(line, allobj)
    allobj = fix_negation(allobj)

    # Label checking
    for en in labeled:
        if en in allobj:
            allobjother = en
            flag = 1

    if (allsub == "") or (allobj == ""):
        return 0

    params_prop['search'] = allsub
    result_pro = []
    json1 = requests.get(url_1, params_prop).json()

    params_en['search'] = allobj
    result_en = []
    json2 = requests.get(url_1, params_en).json()

    if flag == 1:
        params_en['search'] = allobjother
        json3 = requests.get(url_1, params_en).json()

    # Store the returning ID
    for p in json1['search']:
        result_pro.append(p['id'])
    for e in json2['search']:
        result_en.append(e['id'])
    if(flag == 1):
        for j in json3['search']:
            result_en.append(j['id'])

    # Print available answers
    findflag = 0
    for X in result_pro:
        if findflag == 0:
            for Y in result_en:
                data = query(X, Y)
                if (data['results']['bindings'] != []):
                    for item in data['results']['bindings']:
                        for var in item:
                            print("{}".format(item[var]['value']))
                    return 1

    return 0