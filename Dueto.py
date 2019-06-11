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
    json = requests.get(url_api, params_entity).json()
    entities = []
    for result in json['search']:
        # print("{}\t{}\t{}".format(result['id'], result['label'], result['description']))
        entities.append(result['id'])
    return entities


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


def find_answer(properties, entities):
    ans = None
    for entity in entities:
        for property in properties:
            ans = make_query(property, entity)
            if ans is not None:
                return ans
    return ans


# What is the X of Y?
def create_and_fire_queryDueto(line):
    line = nlp(line.rstrip())  # removes newline
    subject = []
    property = []
    flag = 0
    group = []

    for token in line:
        # print(token.text, token.lemma_, token.dep_, token.head.lemma_)
        if token.dep_ == "ROOT" or token.dep_ == "pcomp":
            property.append(token.lemma_)
        if token.dep_ == "nsubj" or (token.dep_ == "compound" and token.head.dep_ == "nsubj"):
            subject.append(token.lemma_)

    prop = str(' '.join(property))
    ent = str(' '.join(subject))

    properties = ['P509']
    entities = find_matches_ent(ent)

    if len(entities) == 0 or len(properties) == 0:
        return 0

    answer = find_answer(properties, entities)
    if answer is None:
        return 0
    else:
        for ans in answer:
            print(ans)

    return 1
