# when where questions
# attempt

import requests
import spacy

url = "https://query.wikidata.org/sparql"
url_api = "https://www.wikidata.org/w/api.php"
params_entity = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}
params_prop = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json', 'type': 'property'}

nlp = spacy.load("en_core_web_sm")


def check_predefined(string):
    if "where" in string and ("take" in string or "hold" in string):
        return ["P276", "P17"]
    if "where" in string and "bear" in string:
        return ["P19", "P27", "P17"]
    if "where" in string and "start" in string:
        return ["P740"]
    if "where" in string and ("found" in string or "form" in string):
        return ["P740"]
    if "come" in string or ("where" in string and "be" in string):
        return ["P19", "P495", "P27", "P17"]
    if "where" in string and ("pass away" in string or "die" in string or "dead" in string):
        return ["P20"]
    if "where" in string and "bury" in string:
        return ["P119"]
    if "where" in string and ("found" in string or "form" in string):
        return ["P740"]
    if "when" in string and "release" in string:
        return ["P577"]
    if "when" in string and ("take" in string or "hold" in string):
        return ["P571"]
    if "when" in string and ("die" in string or "pass away" in string):
        return ["P570"]
    if "when" in string and "bear" in string:
        return ["P569"]
    if "when" in string and "release" in string:
        return ["P577"]
    if "when" in string and ("found" in string or "form" in string or "take" in string):
        return ["P571"]
    if "start" in string or ("when" in string and "invent" in string):
        return ["P571", "P2031", "P575"]
    if "break" in string or "stop" in string:
        return ["P576"]
    if "how" in string and "die" in string:
        return ["P509"]
    return None


def find_matches_ent(string):
    params_entity['search'] = string
    json = requests.get(url_api, params_entity).json()
    entities = []
    for result in json['search']:
        entities.append(result['id'])
    print("in find_matches_ent", entities)
    return entities


def find_matches_prop(string):
    properties = []
    prop = check_predefined(string)
    print("got here?")
    if prop is not None:
        print("prop", prop)
        return prop
    else:
        if "when" in string:
            string = string.replace("when", "")
        if "where" in string:
            string = string.replace("where", "")
        params_prop['search'] = string
        json = requests.get(url_api, params_prop).json()
        for result in json['search']:
            properties.append(result['id'])
    print("in find_matches_prop", properties)
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
    if not answers:
        return None
    else:
        return answers


def find_answer(properties, entities):
    ans = None
    if len(entities) == 0 or len(properties) == 0:
        return None

    for entity in entities:
        for property in properties:
            ans = make_query(property, entity)
            if ans:
                return ans
    return ans


def fix_negation(string):
    if " n't" in string:
        return string.replace(" n't", "n't")
    if " ' " in string:
        return string.replace(" ' ", "' ")
    return string


def fix_redundancy(string):
    if "member" in string and len(string.split()) > 1:
        string = string.replace("member", "")
    if "band" in string and len(string.split()) > 1:
        string = string.replace("band", "")
    if "term" in string and len(string.split()) > 1:
        string = string.replace("term", "")
    if "original" in string and len(string.split()) > 1:
        string = string.replace("original", "")
    if "first" in string and len(string.split()) > 1:
        string = string.replace("first", "")
    if "album" in string and len(string.split()) > 1:
        string = string.replace("album", "")
    if "musician" in string and len(string.split()) > 1:
        string = string.replace("musician", "")
    if "music" in string and len(string.split()) > 1:
        string = string.replace("music", "")
    if "group" in string and len(string.split()) > 1:
        string = string.replace("group", "")
    if string == " ":
        return None
    return string


def fix_special_characters(string):
    if "P!nk" in string:
        string = string.replace("P!nk", "Alecia Beth Moore")
    if "A$AP Rocky" in string:
        string = string.replace("A$AP Rocky", "Lord Flacko")
    if "A$AP" in string:
        string = string.replace("A$AP", "Lord Flacko")
    if "Ke$ha" in string:
        string = string.replace("Ke$ha", "Kesha")
    if "Too $hort" in string:
        string = string.replace("Too $hort", "Too Short")
    if "CD" in string:
        string = string.replace("CD", "Compact disc")
    if "festival" in string:
        string = string.replace("festival", "Festival")
    if "Guns N' Roses" in string:
        string = string.replace("Guns N' Roses", "\"Guns N' Roses\"")
    if "Panic at the Disco" in string:
        string = string.replace("Panic at the Disco", "\"Panic at the Disco\"")
    if "Panic! at the Disco" in string:
        string = string.replace("Panic! at the Disco", "\"Panic at the Disco\"")
    if "festival" in string:
        string = string.replace("festival", "Festival")
    if "Woodstock" in string:
        if "Festival" not in string and "festival" not in string:
            string = string.replace("Woodstock", "Woodstock Festival")

    return string


# example: When/Where was X born?
def create_and_fire_query_WhenWhere(line):
    line = fix_special_characters(line)
    line = nlp(line.rstrip())

    subject = []
    predicate = []
    dobject = []
    extra = []
    poss = []
    appos = []
    label = []
    ans = []
    flag = 0

    for token in line:

        if token.text == "\"":
            flag = 1 - flag
            continue
        if flag == 1:
            extra.append(token.text)
            continue
        if token.dep_ == "ROOT":
            predicate.append(token.lemma_)
        if token.dep_ == "advmod" and (
                token.head.dep_ == "ROOT" or token.head.dep_ == "nsubj" or token.head.dep_ == "dobj" or token.head.dep_ == "auxpass" or token.head.dep_ == "advcl"):
            predicate.append(token.lemma_)
            if (token.head.dep_ == "advcl"):
                predicate.append(token.head.lemma_)

        if token.dep_ == "nummod" and (
                token.head.dep_ == "ROOT" or token.head.dep_ == "nsubj" or token.head.dep_ == "auxpass" or token.head.dep_ == "advcl"):
            predicate.append(token.lemma_)
        if "nsubj" in token.dep_ and token.lemma_ != "-PRON-":
            subject.append(token.lemma_)
        if (
                token.dep_ == "compound" or token.dep_ == "amod" or token.dep_ == "nmod" or token.dep_ == "advcl") and token.head.dep_ == "nsubj":
            subject.append(token.lemma_)
        if token.ent_type_ and token.ent_type_ != "NORP":
            label.append(token.text)

        if "dobj" in token.dep_ or ((token.dep_ == "nmod" or token.dep_ == "compound") and token.head.dep_ == "dobj"):
            dobject.append(token.lemma_)
        if token.dep_ == "poss" or (token.dep_ == "compound" and token.head.dep_ == "poss"):
            poss.append(token.text)
        if (token.dep_ == "appos" and token.head.dep_ == "nsubj") or (
                token.dep_ == "compound" and token.head.dep_ == "appos"):
            appos.append(token.text)

    subject = fix_redundancy(' '.join(subject))
    predicate = fix_redundancy(fix_negation(' '.join(predicate)))
    extra = fix_negation(' '.join(extra))
    dobject = fix_redundancy(' '.join(dobject))
    poss = fix_redundancy(' '.join(poss))
    appos = fix_redundancy(' '.join(appos))
    label = ' '.join(label)

    # new

    if extra and predicate and not ans:
        entities = find_matches_ent(extra)
        properties = find_matches_prop(predicate)
        ans = find_answer(properties, entities)

    if subject and poss and not ans:
        entities = find_matches_ent(poss)
        properties = find_matches_prop(subject)
        ans = find_answer(properties, entities)

    if predicate and label and not ans:
        entities = find_matches_ent(label)
        properties = find_matches_prop(predicate)
        ans = find_answer(properties, entities)

    if dobject and predicate and not ans:
        entities = find_matches_ent(dobject)
        properties = find_matches_prop(predicate)
        ans = find_answer(properties, entities)

    if appos and predicate and not ans:
        entities = find_matches_ent(appos)
        properties = find_matches_prop(predicate)
        ans = find_answer(properties, entities)

    if subject and predicate and not ans:
        entities = find_matches_ent(subject)
        properties = find_matches_prop(predicate)
        ans = find_answer(properties, entities)

    if subject and poss and predicate and not ans:
        entities = find_matches_ent(subject)
        properties = find_matches_prop(predicate)
        ans = find_answer(properties, entities)

    if subject and dobject and predicate and not ans:
        entities = find_matches_ent(dobject)
        properties = find_matches_prop(predicate)
        ans = find_answer(properties, entities)

    if subject and appos and predicate and not ans:
        entities = find_matches_ent(appos)
        properties = find_matches_prop(predicate)
        ans = find_answer(properties, entities)

    if ans:
        for a in ans:
            print(str(a))
        return 1
    return 0

    return ans
