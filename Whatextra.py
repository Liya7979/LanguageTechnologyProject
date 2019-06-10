#!/usr/bin/env python3
import requests
import sys
import spacy
import re

nlp = spacy.load("en_core_web_sm")

url_1 = "https://www.wikidata.org/w/api.php"
url_2 = "https://query.wikidata.org/sparql"

# Parameters for entity and property searching respectively
params_prop = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json', 'type': 'property'}
params_en = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}

def special_checking(line,allobj):
    if "A-Ha" in line:
        allobj = "A-Ha"
    if "BTS" in line:
        allobj = "BTS"
    if "The Script" in line:
        allobj = "The Script"
    return allobj

def check_predefined(string):
    if ("What" in string or "what" in string) and ("occupations" in string or "occupation" in string):
        return ["P106"]
    if ("What" in string or "what" in string) and ("genres" in string or "genre" in string):
        return ["P136"]
    if ("What" in string or "what" in string) and "date" in string and "born" in string:
        return ["P569"]
    if ("What" in string or "what" in string) and "date" in string and ("die" in string or "died" in string or "dies" in string):
        return ["P570"]
    if ("What" in string or "what" in string) and "place" in string and "born" in string:
        return ["P19"]
    if ("What" in string or "what" in string) and "place" in string and ("die" in string or "died" in string or "dies" in string or "death" in string):
        return ["P20"]
    if ("What" in string or "what" in string) and "cause" in string and ("die" in string or "died" in string or "dies" in string or "death" in string):
        return ["P509"]
    if ("What" in string or "what" in string) and ("instrument" in string or "instruments" in string):
        return ["P1303"]
    if ("What" in string or "what" in string) and ("bands"in string or "band" in string) and ("play" in string or "played" in string or "plays" in string):
        return ["P527","P463","P361"]
    if ("What" in string or "what" in string) and "country" in string and "from":
        return ["P27","P495"]
    if ("What" in string or "what" in string) and "record label" in string:
        return ["P264"]

# query with wikidata
def query(prop, entity):
    query = '''
        SELECT ?NameLabel WHERE{
            wd:%s wdt:%s ?Name .
            SERVICE wikibase:label { bd:serviceParam wikibase:language "en".}
    }''' % (entity, prop)
    data = requests.get(url_2, params={'query': query, 'format': 'json'}).json()
    return data

def create_and_fire_queryWhatextra(line):
    parse = nlp(line.rstrip())
    obj = []
    labeled = []
    flag = 0

    for ent in parse.ents:
        if (ent.label_ != []):
            labeled.append(ent.lemma_)

    for token in parse:
        #print("\t".join((token.text, token.dep_)))
        if token.text == "The":
            obj.append(token.text)
        if token.dep_ == "nsubj" or token.dep_ == "attr":
            obj.append(token.text)
        if token.dep_ == "compound" and (token.head.dep_ == "nsubj" or token.head.dep_ == "attr"):
            obj.append(token.text)

    allobj = (" ".join(obj))
    # Special entity checking
    allobj =special_checking(line,allobj)

    # Label checking
    for en in labeled:
        if en in allobj:
            allobjother = en
            flag = 1

    # If not, back to the main function
    if allobj =="":
        return 0

    result_pro = check_predefined(line)
    if not result_pro:
        return 0

    params_en['search'] = allobj
    result_en = []
    json2 = requests.get(url_1, params_en).json()

    if flag == 1:
        params_en['search'] = allobjother
        json3 = requests.get(url_1, params_en).json()

    # Store the returning IDs
    for e in json2['search']:
        result_en.append(e['id'])
    if (flag == 1):
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
