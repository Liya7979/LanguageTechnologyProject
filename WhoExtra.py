#!/usr/bin/env python3
import re

import requests
import spacy

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
    "where bear": "place of birth",
    "when die": "date of death",
    "where die": "place of death",
    "when bear": "date of birth",
    "child": "children",
    "perform": "performer",
    "write": "composer",
    "compose": "composer",
    "influence": "influenced by",
    "sing": "performer",
    "found": "founded by",
    "produce": "producer",
    "kill": "killer",
    "teach": "student of",
    "in": "has part",
    "create": "creator",
    "invent": "inventor"
}


# Entity Special cases
def special_checking(line, allobj):
    if "A-Ha" in line:
        allobj = "A-Ha"
    if "BTS" in line:
        allobj = "BTS"
    if "The Script" in line:
        allobj = "The Script"
    if "The Eagles" in line:
        allobj = "The Eagles"
    if "AC/DC" in line:
        allobj = "AC/DC"
    if "Jackson 5" in line:
        allobj = "Jackson 5"
    if "U2" in line:
        allobj = "U2"
    if "MF DOOM" in line:
        allobj = "MF DOOM"
    if "Wu-Tang Clan" in line:
        allobj = "Wu-Tang Clan"
    return allobj


# Negation fix
def fix_negation(string):
    if "n't" in string:
        return string.replace(" n't", "n't")
    return string


def fix_redundancy(string):
    if "who" in string and len(string.split()) > 1:
        string = string.replace("who", "")
    if "Who" in string and len(string.split()) > 1:
        string = string.replace("Who", "")
    if "single" in string and len(string.split()) > 1:
        string = string.replace("single", "")
    if "the" in string and len(string.split()) > 1:
        string = string.replace("the", "")
    if "song" in string and len(string.split()) > 1:
        string = string.replace("song", "")
    if "rock" in string and len(string.split()) > 1:
        string = string.replace("rock", "")
    if "pop" in string and len(string.split()) > 1:
        string = string.replace("pop", "")
    if "jazz" in string and len(string.split()) > 1:
        string = string.replace("jazz", "")
    if "original" in string and len(string.split()) > 1:
        string = string.replace("original", "")
    if "first" in string and len(string.split()) > 1:
        string = string.replace("first", "")
    if "musical" in string and len(string.split()) > 1:
        string = string.replace("musical", "")
    if "musician" in string and len(string.split()) > 1:
        string = string.replace("musician", "")
    if "music" in string and len(string.split()) > 1:
        string = string.replace("music", "")
    if "genre" in string and len(string.split()) > 1:
        string = string.replace("genre", "")
    if "song" in string and len(string.split()) > 1:
        string = string.replace("song", "")
    if "member" in string and len(string.split()) > 1:
        string = string.replace("member", "")
    if "band" in string and len(string.split()) > 1:
        string = string.replace("band", "")
    if "album" in string and len(string.split()) > 1:
        string = string.replace("album", "")
    if "group" in string and len(string.split()) > 1:
        string = string.replace("group", "")

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


def create_and_fire_queryWhoextra(line):
    parse = nlp(line.rstrip())
    subj = []
    obj = []
    labeled = []
    type1 = 0
    type2 = 0
    flag = 0

    for ent in parse.ents:
        if (ent.label_ != []):
            labeled.append(ent.lemma_)
            flag = 1

    for token in parse:
        # print("\t".join((token.text, token.dep_)))
        if (type1 == 1):
            obj.append(token.text)

        if (type2 == 1):
            obj.append(token.text)

        if (token.dep_ == "ROOT") and ((token.lemma_) in prop_dict):
            subj.append(token.lemma_)
            type1 = 1

        if (token.lemma_ == "in"):
            subj.append(token.lemma_)
            type2 = 1

    if (type1 == 0 and type2 == 0):
        return 0

    allsub = (" ".join(subj))
    allobj = (" ".join(obj))

    if allsub in prop_dict:
        allsub = prop_dict[allsub]

    allobj = fix_redundancy(allobj)
    allobj = allobj.strip()
    allobj = re.sub("^[^a-zA-Z]", "", allobj)
    allobj = re.sub("[^a-zA-Z]$", "", allobj)

    allobj = allobj.strip()

    # fix
    allobj = special_checking(line, allobj)
    allobj = fix_negation(allobj)

    if (allsub == "") or (allobj == ""):
        return 0

    params_prop['search'] = allsub
    result_pro = []
    json1 = requests.get(url_1, params_prop).json()

    params_en['search'] = allobj
    result_en = []
    json2 = requests.get(url_1, params_en).json()

    if flag == 1:
        allobjother = (" ".join(labeled))
        params_en['search'] = allobjother
        json3 = requests.get(url_1, params_en).json()
        for j in json3['search']:
            result_en.append(j['id'])

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
                            print("{}".format(item[var]['value']))
                    return 1

    return 0
