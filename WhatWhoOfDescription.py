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
    if "what" in string and len(string.split()) > 1:
        string = string.replace("what", "")
    if "What" in string and len(string.split()) > 1:
        string = string.replace("What", "")
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


def what_is_x(string):
    params_en['search'] = string
    json = requests.get(url_1, params_en).json()
    entities = []
    if not json:
        return entities

    if not ['description'] in json['search']:
        return entities

    for result in json['search']:
        # print("{}\t{}\t{}".format(result['id'], result['label'], result['description']))
        if result['description']:
            entities.append(result['description'])
        if entities:
            break
    return entities


def create_and_fire_queryWhatWhoOfD(line):
    parse = nlp(line.rstrip())
    subj = []
    obj = []
    labeled = []
    flag = 0
    for ent in parse.ents:
        if (ent.label_ != []):
            labeled.append(ent.lemma_)
            flag = 1
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
                        obj.append(t2.text)
                    if t2.dep_ == "compound" and t2.head.dep_ == "pobj":
                        obj.append(t2.text)

    if not subj:
        return 0

    if not obj:
        answer = what_is_x(subj)
        if answer:
            for x in answer:
                print("\t", x)
            return 1
        return 0

    allsub = (" ".join(subj))
    allobj = (" ".join(obj))

    allobj = (" ".join(obj))
    allobj = fix_redundancy(allobj)
    allobj = allobj.strip()
    allobj = re.sub("^[^a-zA-Z]", "", allobj)
    allobj = re.sub("[^a-zA-Z]$", "", allobj)

    # fix
    allobj = special_checking(line, allobj)
    allobj = fix_negation(allobj)

    # Check up with dictionary
    if allsub in prop_dict:
        allsub = prop_dict[allsub]

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
    total_ans = []
    for X in result_pro:
        if findflag == 0:
            for Y in result_en:
                data = query(X, Y)
                if (data['results']['bindings'] != []):
                    for item in data['results']['bindings']:
                        for var in item:
                            total_ans.append("{}".format(item[var]['value']))
                    print("\t",'\t'.join(total_ans))
                    return 1

    return 0
