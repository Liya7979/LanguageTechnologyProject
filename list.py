#!/usr/bin/env python3
import requests
import spacy

url = "https://query.wikidata.org/sparql"
url_api = "https://www.wikidata.org/w/api.php"
params_entity = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}
params_prop = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json', 'type': 'property'}

nlp = spacy.load("en_core_web_sm")


def find_matches_ent(string):
    params_entity['search'] = string
    if string == "":
        return None
    json = requests.get(url_api, params_entity).json()
    entities = []
    for result in json['search']:
        # print("{}\t{}\t{}".format(result['id'], result['label'], result['description']))
        entities.append(result['id'])
    return entities


def find_matches_prop(string):
    properties = []
    prop = check_predefined(string)
    if len(prop) != 0:
        return prop
    else:
        params_prop['search'] = string
        if string == "":
            return None
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
    if len(answers) == 0:
        return None
    else:
        return answers


def check_predefined(string):
    prop = []
    if "member" in string:
        prop.append('P527')
    if string == "real name":
        prop.append('P1477')
    if string == "from where":
        prop.append('P495')
    return prop


def define_entity_term(subject):
    entity = []
    for item in subject:
        entity.append(item.lemma_)
    if len(entity) > 1:
        ent = ' '.join(entity)
    else:
        ent = str(entity[0])
    return ent


def define_property_term(predicate):
    property = []
    for item in predicate:
        property.append(item.text)
    if len(property) > 1:
        prop = ' '.join(property)
    else:
        prop = str(property[0])
    return prop


def find_answer(properties, entities):
    ans = None
    if len(entities) == 0 or len(properties) == 0:
        return None

    for entity in entities:
        for property in properties:
            ans = make_query(property, entity)
            if ans is not None:
                return ans
    return ans


# Name the members of X
def create_and_fire_query_dobj(line):
    line = nlp(line.rstrip())
    pobj = []
    dobject = []
    for token in line:
        # print(token.text, token.lemma_, token.dep_, token.head.lemma_)
        if "dobj" in token.dep_:
            dobject.append(token)
        if (token.dep_ == "compound" or token.dep_ == "amod") and token.head.dep_ == "dobj":
            dobject.append(token)

    flag = 0
    group = []
    for t in line:
        if t.dep_ == "prep" and flag == 0 and len(pobj) == 0:
            group.append(t)
        if t.dep_ == "pobj" and flag == 1:
            dobject = dobject + pobj
            pobj = []
            flag = 0
        if t.dep_ == "pobj" and flag == 0:
            pobj = pobj + group
            pobj.append(t)
            group = []
            flag = 1
        if (t.dep_ == "compound" or t.dep_ == "nummod") and t.head.dep_ == "pobj":
            group.append(t)

    if len(pobj) > 1:
        if pobj[0].dep_ == "prep":
            del pobj[0]

    prop = define_property_term(dobject)
    ent = define_entity_term(pobj)

    properties = find_matches_prop(prop)
    entities = find_matches_ent(ent)

    ans = find_answer(properties, entities)

    if ans:
        print(' '.join(ans))
        return 1
    return 0
