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


def fix_redundancy(string):
    if "what" in string and len(string.split()) > 1:
        string = string.replace("what", "")
    if "What" in string and len(string.split()) > 1:
        string = string.replace("What", "")
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


def check_predefined(string):
    if ("What" in string or "what" in string) and (
            "partner" in string or "spouse" in string or "partner" in string or "partners" in string):
        return ["P451"]
    if ("What" in string or "what" in string) and ("made of" in string):
        return ["P186"]
    if ("What" in string or "what" in string) and ("date" in string or "year" in string) and (
            "dissolve" in string or "dissolved" in string):
        return ["P576"]
    if ("What" in string or "what" in string) and ("university" in string or "education" in string):
        return ["P69"]
    if ("What" in string or "what" in string) and ("date" in string or "year" in string) and (
            "inception" in string or "founded" in string or "invented" in string):
        return ["P571"]
    if ("What" in string or "what" in string) and ("city" in string or "country" in string) and (
            "founded" in string or "invented" in string):
        return ["P740", "P495"]
    if ("What" in string or "what" in string) and ("city" in string) and ("born" in string):
        return ["P19"]
    if ("What" in string or "what" in string) and ("occupations" in string or "occupation" in string):
        return ["P106"]
    if ("What" in string or "what" in string) and (
            "genres" in string or "genre" in string or "kind of music" in string or "music" in string):
        return ["P136"]
    if ("What" in string or "what" in string) and ("date" in string or "year" in string) and "born" in string:
        return ["P569"]
    if ("What" in string or "what" in string) and ("date" in string or "year" in string) and (
            "die" in string or "died" in string or "dies" in string or "pass away" in string or "passed away" in string):
        return ["P570"]
    if ("What" in string or "what" in string) and "place" in string and "born" in string:
        return ["P19"]
    if ("What" in string or "what" in string) and "place" in string and (
            "die" in string or "died" in string or "dies" in string or "death" in string):
        return ["P20"]
    if ("What" in string or "what" in string) and "cause" in string and (
            "die" in string or "died" in string or "dies" in string or "death" in string):
        return ["P509"]
    if ("What" in string or "what" in string) and ("instrument" in string or "instruments" in string):
        return ["P1303"]
    if ("What" in string or "what" in string) and ("bands" in string or "band" in string) and (
            "play" in string or "played" in string or "plays" in string or "perform" in string or "performs" in string or "performed" in string):
        return ["P463", "P361", "P527"]
    if ("What" in string or "what" in string) and "country" in string and "from":
        return ["P17", "P27", "P495"]
    if ("What" in string or "what" in string) and "record label" in string:
        return ["P264"]
    if ("What" in string or "what" in string) and ("award" in string or "awards" in string):
        return ["P166"]
    if ("What" in string or "what" in string) and ("kills" in string or "killed" in string or "killer" in string):
        return ["P157", "P509"]
    if ("What" in string or "what" in string) and ("named after" in string):
        return ["P138"]


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
            flag = 1

    for token in parse:
        # print("\t".join((token.text, token.dep_)))
        if token.text == "The":
            obj.append(token.text)
        if token.dep_ == "nsubj" or token.dep_ == "attr" or token.dep_ == "dobj":
            obj.append(token.text)
        if token.dep_ == "compound" and (
                token.head.dep_ == "nsubj" or token.head.dep_ == "attr" or token.head.dep_ == "dobj"):
            obj.append(token.text)

    allobj = (" ".join(obj))
    allobj = fix_redundancy(allobj)
    allobj = allobj.strip()
    allobj = re.sub("^[^a-zA-Z]", "", allobj)
    allobj = re.sub("[^a-zA-Z]$", "", allobj)

    # Special entity checking
    allobj = special_checking(line, allobj)

    # If not, back to the main function
    if allobj == "":
        return 0

    result_pro = check_predefined(line)
    if not result_pro:
        return 0

    params_en['search'] = allobj
    result_en = []
    json2 = requests.get(url_1, params_en).json()

    if flag == 1:
        allobjother = (" ".join(labeled))
        params_en['search'] = allobjother
        json3 = requests.get(url_1, params_en).json()
        for j in json3['search']:
            result_en.append(j['id'])

    # Store the returning IDs
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
