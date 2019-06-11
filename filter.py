#!/usr/bin/env python3
import requests
import spacy

url = "https://query.wikidata.org/sparql"
url_api = "https://www.wikidata.org/w/api.php"
params_entity = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}
params_prop = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json', 'type': 'property'}

nlp = spacy.load("en_core_web_sm")


def check_predefined(string):
    if "be" in string or "who" in string or "join" in string:
        return ["P527"]
    return None


def find_matches_ent(string):
    params_entity['search'] = string
    json = requests.get(url_api, params_entity).json()
    entities = []
    for result in json['search']:
        entities.append(result['id'])
    return entities


def find_matches_prop(string):
    properties = []
    prop = check_predefined(string)
    if prop is not None:
        return prop
    else:
        if "when" in string:
            string = string.replace("when", "")
        if "where" in string:
            string = string.replace("where", "")
        if string == "":
            return None
        params_prop['search'] = string
        json = requests.get(url_api, params_prop).json()
        for result in json['search']:
            properties.append(result['id'])
    return properties


def make_query_before(property, entity, year):
    answers = []
    query = '''
		SELECT ?answerLabel WHERE { 
			wd:''' + entity + ''' p:''' + property + ''' ?statement.
			?statement ps:''' + property + ''' ?answer.
			?statement pq:P580 ?start.
			FILTER (?start < "''' + year + '''-01-01T00:00:00Z"^^xsd:dateTime)
			SERVICE wikibase:label {
				bd:serviceParam wikibase:language "en" .
			}
		}'''
    # print(query)
    data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    for item in data['results']['bindings']:
        for var in item:
            answers.append(item[var]['value'])
    if not answers:
        return None
    else:
        return answers


def make_query_after(property, entity, year):
    answers = []
    query = '''
		SELECT ?answerLabel WHERE { 
			wd:''' + entity + ''' p:''' + property + ''' ?statement.
			?statement ps:''' + property + ''' ?answer.
			?statement pq:P580 ?start.
			FILTER (?start >= "''' + year + '''-01-01T00:00:00Z"^^xsd:dateTime)
			SERVICE wikibase:label {
				bd:serviceParam wikibase:language "en" .
			}
		}'''
    data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    for item in data['results']['bindings']:
        for var in item:
            answers.append(item[var]['value'])
    if not answers:
        return None
    else:
        return answers


def make_query_between(property, entity, date):
    year1 = date.split(" ")[1]
    year2 = date.split(" ")[3]
    answers = []
    query = '''
		SELECT ?answerLabel WHERE { 
			wd:''' + entity + ''' p:''' + property + ''' ?statement.
			?statement ps:''' + property + ''' ?answer.
			?statement pq:P580 ?start.
			?statement pq:P582 ?end.
			FILTER (?start <= "''' + year1 + '''-01-01T00:00:00Z"^^xsd:dateTime) 
			FILTER (?end >= "''' + year2 + '''-01-01T00:00:00Z"^^xsd:dateTime)
			SERVICE wikibase:label {
				bd:serviceParam wikibase:language "en" .
			}
		}'''
    data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    for item in data['results']['bindings']:
        for var in item:
            answers.append(item[var]['value'])
    if not answers:
        return None
    else:
        return answers


def find_answer(properties, entities, prep, date):
    if not entities or not properties:
        return None
    ans = None
    for entity in entities:
        for property in properties:
            if prep == 2:
                ans = make_query_before(property, entity, date)
            if prep == 1:
                ans = make_query_after(property, entity, date)
            if prep == 3:
                ans = make_query_between(property, entity, date)
            if ans:
                return ans
    return ans


def fix_negation(string):
    if "be " in string and len(string.split()) > 1:
        return string.replace("be ", "")
    if " n't" in string:
        return string.replace(" n't", "n't")
    return string


def fix_redundancy(string):
    if "which" in string:
        string = string.replace("which", "")
        if string == " ":
            return None
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


# example: When/Where was X born?
def create_and_fire_query_filter(line):
    line = line.rstrip()
    line = nlp(line)

    subject = []
    predicate = []
    dobject = []
    extra = []
    poss = []
    appos = []
    pobject = []
    labeled = []
    attr = []
    pcomp = []
    oprd = []
    date = []

    flag = 0
    prep = 0
    for token in line:
        if token.text == "\"":
            flag = 1 - flag
            continue
        if flag == 1:
            extra.append(token.text)
            continue
        if token.dep_ == "oprd" or (token.dep_ == "compound" and token.head.dep_ == "oprd"):
            oprd.append(token.text)
        if token.ent_type_:
            if token.ent_type_ == "DATE" or token.ent_type_ == "CARDINAL":
                date.append(token.text)
            else:
                labeled.append(token.text)
            continue
        if token.dep_ == "prep" and token.lemma_ == "after":
            prep = 1
        if token.dep_ == "prep" and token.lemma_ == "before":
            prep = 2
        if "nsubj" in token.dep_ and token.lemma_ != "-PRON-":
            subject.append(token.lemma_)
        if token.dep_ == "poss" and "nsubj" in token.head.dep_:
            subject.append(token.text)
        if (
                token.dep_ == "compound" or token.dep_ == "amod" or token.dep_ == "nmod" or token.dep_ == "advcl") and "nsubj" in token.head.dep_:
            subject.append(token.lemma_)
        if token.dep_ == "ROOT" or (token.dep_ == "attr" and token.head.dep_ == "ROOT"):
            predicate.append(token.lemma_)
        if (token.dep_ == "advmod" or token.dep_ == "nummod") and (
                token.head.dep_ == "ROOT" or token.head.dep_ == "auxpass" or token.head.dep_ == "advcl"):
            predicate.append(token.lemma_)
        if "dobj" in token.dep_ or ((token.dep_ == "nmod" or token.dep_ == "compound") and token.head.dep_ == "dobj"):
            dobject.append(token.lemma_)
        if token.dep_ == "poss" or (token.dep_ == "compound" and token.head.dep_ == "poss"):
            poss.append(token.text)
        if (token.dep_ == "appos" and ("nsubj" in token.head.dep_ or token.head.dep_ == "attr")) or (
                token.dep_ == "compound" and token.head.dep_ == "appos"):
            appos.append(token.text)
        if "pobj" in token.dep_ or ((token.dep_ == "nmod" or token.dep_ == "compound") and token.head.dep_ == "pobj"):
            pobject.append(token.lemma_)
        if token.dep_ == "attr" or (token.dep_ == "compound" and token.head.dep_ == "attr"):
            attr.append(token.lemma_)
        if token.dep_ == "pcomp" or (token.dep_ == "compound" and token.head.dep_ == "pcomp"):
            pcomp.append(token.lemma_)

    predicate = fix_redundancy(fix_negation(' '.join(predicate)))
    subject = fix_redundancy(' '.join(subject))
    extra = fix_negation(' '.join(extra))
    dobject = fix_redundancy(' '.join(dobject))
    poss = fix_redundancy(' '.join(poss))
    appos = fix_redundancy(' '.join(appos))
    pobject = fix_redundancy(' '.join(pobject))
    labeled = fix_redundancy(' '.join(labeled))
    attr = fix_redundancy(' '.join(attr))
    pcomp = fix_redundancy(' '.join(pcomp))
    oprd = fix_redundancy(' '.join(oprd))
    date = ' '.join(date)

    properties = []
    entities = []
    ans = []

    if ("between" in date):
        prep = 3
    if not ans and predicate and pobject and date:
        entities = find_matches_ent(pobject)
        properties = find_matches_prop(predicate)
        ans = find_answer(properties, entities, prep, date)
    if not ans and predicate and labeled and date:
        entities = find_matches_ent(labeled)
        properties = find_matches_prop(predicate)
        ans = find_answer(properties, entities, prep, date)
    if not ans and predicate and extra and date:
        entities = find_matches_ent(extra)
        properties = find_matches_prop(predicate)
        ans = find_answer(properties, entities, prep, date)
    if ans:
        total_ans = '\t'.join(ans)
        print("\t", total_ans)
        return 1
    return 0
