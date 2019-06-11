from datetime import date
from datetime import datetime

import requests
import spacy

url = "https://query.wikidata.org/sparql"
url_api = "https://www.wikidata.org/w/api.php"
params_entity = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}
params_prop = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json', 'type': 'property'}
nlp = spacy.load("en_core_web_sm")


def check_predefined(string):
    if "call" in string:
        return ['P1535', 'P1449']
    if "long" in string:
        return ['P2047']
    if "tall" in string:
        return ['P2048']
    if "fast" in string:
        return ['P1725']
    if "die" in string:
        return ['P509', 'P1196']
    if "found" in string:
        return ['P112']
    return None


def find_matches_ent(string):
    params_entity['search'] = string
    json = requests.get(url_api, params_entity).json()
    entities = []
    for result in json['search']:
        # print("{}\t{}\t{}".format(result['id'], result['label'], result['description']))
        entities.append(result['id'])
    return entities


def find_matches_prop(string):
    prop = check_predefined(string)
    if prop is not None:
        return prop
    else:
        if string == "how":
            return None
        properties = []
        params_prop['search'] = string
        # print("property in find_matches", string)
        json = requests.get(url_api, params_prop).json()
        for result in json['search']:
            # print("{}\t{}\t{}".format(result['id'], result['label'], result['description']))
            properties.append(result['id'])
    return properties


def make_query(property, entity):
    answers = []
    query = '''
		SELECT ?answerLabel WHERE { 
			wd:''' + entity + ''' wdt:''' + property + ''' ?answer.
			SERVICE wikibase:label {
				bd:serviceParam wikibase:language "en" .
			}
		}'''
    data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    for item in data['results']['bindings']:
        for var in item:
            answers.append(item[var]['value'])
    return answers


def compute_age(birthday, death):
    if not birthday or not death:
        return 0
    bday = str(birthday[0])
    if "T00:00:00Z" in bday:
        bday = bday.replace("T00:00:00Z", "")
    dday = str(death[0])
    b = datetime.strptime(bday[0:4] + "/" + bday[5:7] + "/" + bday[8:10], "%Y/%m/%d")
    d = datetime.strptime(dday[0:4] + "/" + dday[5:7] + "/" + dday[8:10], "%Y/%m/%d")
    print((int(((d - b).days) / 365)))
    return 1


def find_age(entities):
    for entity in entities:
        birthday = make_query("P569", entity)
        if not birthday:
            birthday = make_query("P571", entity)
            if birthday:
                death = make_query("P576", entity)
                if death:
                    return compute_age(birthday, death)
                else:
                    today = date.today()
                    today = [today]
                    return compute_age(birthday, today)
            else:
                return 0
        if birthday:
            death = make_query("P570", entity)
            if death:
                return compute_age(birthday, death)
            else:
                today = date.today()
                today = [today]
                return compute_age(birthday, today)
    return 0


def find_answer(properties, entities):
    if not entities or not properties:
        return None
    ans = None
    for entity in entities:
        for property in properties:
            ans = make_query(property, entity)
            if ans is not None:
                return ans
    return ans


def fix_redundancy(string):
    if "song" in string:
        string = string.replace("song", "")
    if "member" in string:
        string = string.replace("member", "")
    if "band" in string:
        string = string.replace("band", "")
    if "term" in string:
        string = string.replace("term", "")
    if "original" in string:
        string = string.replace("original", "")
    if "first" in string:
        string = string.replace("first", "")
    if "album" in string:
        string = string.replace("album", "")
    if "musician" in string:
        string = string.replace("musician", "")
    if "music" in string:
        string = string.replace("music", "")
    if "group" in string:
        string = string.replace("group", "")
    if "someone" in string:
        string = string.replace("someone", "")
    if string == " ":
        return None
    return string


def create_and_fire_query_How(line):
    line = nlp(line.rstrip())
    subject = []
    predicate = []
    adv = []
    dobject = []
    pobject = []
    poss = []

    flag = 0
    for token in line:
        if token.text == "\"":
            flag = 1 - flag
            continue
        if flag == 1:
            subject.append(token.text)
            continue
        if "nsubj" in token.dep_ and token.lemma_ != "-PRON-":
            subject.append(token.lemma_)
        if (token.dep_ == "compound" or token.dep_ == "amod" or token.dep_ == "appos") and "nsubj" in token.head.dep_:
            subject.append(token.lemma_)
        if token.dep_ == "compound" and token.head.dep_ == "appos":
            subject.append(token.lemma_)
        if (token.dep_ == "acomp" or token.dep_ == "advmod") and token.head.dep_ == "ROOT":
            adv.append(token.lemma_)
        if token.dep_ == "ROOT":
            predicate.append(token.lemma_)
        if "dobj" in token.dep_ or ((token.dep_ == "nmod" or token.dep_ == "compound") and token.head.dep_ == "dobj"):
            dobject.append(token.lemma_)
        if "pobj" in token.dep_ or ((token.dep_ == "nmod" or token.dep_ == "compound") and token.head.dep_ == "pobj"):
            pobject.append(token.lemma_)
        if token.dep_ == "poss" or (token.dep_ == "compound" and token.head.dep_ == "poss"):
            poss.append(token.text)

    subject = fix_redundancy(' '.join(subject))
    adv = ' '.join(adv)
    predicate = ' '.join(predicate)
    dobject = fix_redundancy(' '.join(dobject))
    pobject = fix_redundancy(' '.join(pobject))
    poss = fix_redundancy(' '.join(poss))

    # print("subject", subject)
    # print("predicate", predicate)
    # print("adv", adv)
    # print("dobject", dobject)
    # print("pobject", pobject)
    # print("poss", poss)

    entities = []
    properties = []
    ans = []

    if subject:
        entities = find_matches_ent(subject)
    if not entities and dobject:
        entities = find_matches_ent(dobject)
    if "old" in adv:
        return find_age(entities)

    if poss and dobject:
        properties = find_matches_prop(dobject)
    if poss and subject and not dobject:
        properties = find_matches_prop(subject)
        entities = find_matches_ent(poss)
    if not properties and adv:
        properties = find_matches_prop(adv)
    if not properties and predicate:
        properties = find_matches_prop(predicate)
    if not properties and pobject:
        properties = find_matches_prop(pobject)
    if properties and entities:
        ans = find_answer(properties, entities)
    if not ans:
        if pobject:
            properties = find_matches_prop(pobject)
    ans = find_answer(properties, entities)
    if not ans:
        if dobject:
            entities = find_matches_ent(dobject)
    ans = find_answer(properties, entities)
    if not ans:
        return 0
    else:
        for a in ans:
            print(a)
    return 1
