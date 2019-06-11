#!/usr/bin/env python3
import requests
import spacy

url = "https://query.wikidata.org/sparql"
url_api = "https://www.wikidata.org/w/api.php"
params_entity = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}
params_prop = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json', 'type': 'property'}

nlp = spacy.load("en_core_web_sm")


def check_predefined(string):
    if "base" in string:
        return ["P4969"]
    if "label" in string:
        return ["P264"]
    if "school" in string or "university" in string or "educate" in string:
        return ["P69"]
    if "name" in string and "stage" in string:
        return ["P742"]
    if "pet" in string:
        return ["P1429"]
    if "name" in string:
        return ["P1477", "P735"]
    if "record label" in string:
        return ["P264"]
    if "release" in string:
        return ["P577"]
    if "break" in string or "stop" in string:
        return ["P576"]
    if "city" in string or "town" in string:
        return ["P740", "P19", "P470", "P131", "P495"]
    if "bear" in string:
        return ["P569", "P19", "P1477", "P735"]
    if "band" in string or "member" in string or "part" in string:
        return ["P463", "P361", "P527"]
    if "be" in string:
        return ["P175", "P19", "P470", "P131", "P495"]
    if "found" in string or "form" in string:
        return ["P112", "P571", "P127"]
    if "perform" in string or "album" in string:
        return ["P361", "P1729"]
    if "start" in string or "invent" in string or "century" in string or "year" in string or "date" in string:
        return ["P571", "P2031", "P575"]
    if "lead" in string or "singer" in string or "guitarist" in string or "drummer" in string:
        return ["P527"]
    if "how" in string and "die" in string:
        return ["P509", "P1196"]
    if "superclass" in string or "instance" in string or "type" in string:
        return ["P279", "P31"]
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
    if prop:
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
    if not entities or not properties:
        return None
    ans = None
    flag = 0
    if properties == ["P527"]:
        flag = 1
    for entity in entities:
        for property in properties:
            ans = make_query(property, entity)
            if ans:
                if flag == 1:
                    return [ans[0]]
                return ans
    return ans


def fix_negation(string):
    if "be " in string and len(string.split()) > 1:
        return string.replace("be ", "")
    if " n't" in string:
        return string.replace(" n't", "n't")
    if "'s" in string:
        return string.replace("'s", "")
    return string


def fix_redundancy(string):
    if "which" in string:
        string = string.replace("which", "")
        if string == "":
            return None
    if "who" in string:
        string = string.replace("who", "")
        if string == "":
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
def create_and_fire_query_adv(line):
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

    flag = 0
    for token in line:
        # print(token.text, token.lemma_, token.dep_, token.head.lemma_)
        if token.text == "\"":
            flag = 1 - flag
            continue
        if flag == 1:
            extra.append(token.text)
            continue
        if token.dep_ == "oprd" or (token.dep_ == "compound" and token.head.dep_ == "oprd"):
            oprd.append(token.text)
        if token.ent_type_:  # == "PERSON" or token.ent_type_ == "ONG" or token.ent_type_ == "WORK_OF_ART":
            labeled.append(token.text)
            continue
        if "nsubj" in token.dep_ and token.lemma_ != "-PRON-":
            subject.append(token.lemma_)
        if token.dep_ == "poss" and "nsubj" in token.head.dep_:
            subject.append(token.text)
        if (
                token.dep_ == "compound" or token.dep_ == "amod" or token.dep_ == "nmod" or token.dep_ == "advcl") and "nsubj" in token.head.dep_:
            subject.append(token.lemma_)
        if token.dep_ == "ROOT":
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
        if "pobj" in token.dep_ or ((
                                            token.dep_ == "nmod" or token.dep_ == "compound" or token.dep_ == "amod") and token.head.dep_ == "pobj"):
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
    labeled = fix_negation(fix_redundancy(' '.join(labeled)))
    attr = fix_redundancy(' '.join(attr))
    pcomp = fix_redundancy(' '.join(pcomp))
    oprd = fix_redundancy(' '.join(oprd))

    # print("predicate", predicate)
    # print("subject", subject)
    # print("extra", extra)
    # print("dobject", dobject)
    # print("poss", poss)
    # print("appos", appos)
    # print("pobject", pobject)
    # print("labeled", labeled)
    # print("attr", attr)
    # print("pcomp", pcomp)
    # print("oprd", oprd)

    properties = []
    entities = []
    ans = []

    # ent = oprd; prop = predicate
    if not ans and oprd and predicate:
        entities = find_matches_ent(oprd)
        properties = find_matches_prop(predicate)
        ans = find_answer(properties, entities)
    # ent = extra; prop = pcomp
    if not ans and extra and pcomp:
        properties = find_matches_prop(pcomp)
        entities = find_matches_ent(extra)
        ans = find_answer(properties, entities)
    # ent = extra; prop = pobject
    if not ans and pobject and extra:
        entities = find_matches_ent(extra)
        properties = find_matches_prop(pobject)
        ans = find_answer(properties, entities)
    # ent = extra; prop = subject
    if not ans and extra and subject:
        properties = find_matches_prop(subject)
        entities = find_matches_ent(extra)
        ans = find_answer(properties, entities)
    # ent = extra; prop = predicate
    if not ans and predicate and extra:
        entities = find_matches_ent(extra)
        properties = find_matches_prop(predicate)
        ans = find_answer(properties, entities)
    # ent = labeled; prop = pcomp
    if not ans and labeled and pcomp:
        entities = find_matches_ent(labeled)
        properties = find_matches_prop(pcomp)
        ans = find_answer(properties, entities)
    # ent = labeled; prop = pobject
    if not ans and pobject and labeled:
        entities = find_matches_ent(labeled)
        properties = find_matches_prop(pobject)
        ans = find_answer(properties, entities)
    # ent = labeled; prop = subject
    if subject and labeled and not ans:
        entities = find_matches_ent(labeled)
        properties = find_matches_prop(subject)
        ans = find_answer(properties, entities)
    # ent = labeled; prop = attr
    if not ans and labeled and attr:
        properties = find_matches_prop(attr)
        entities = find_matches_ent(labeled)
        ans = find_answer(properties, entities)
    # ent = labeled; prop = predicate
    if not ans and predicate and labeled:
        entities = find_matches_ent(labeled)
        properties = find_matches_prop(predicate)
        ans = find_answer(properties, entities)
    # ent = dobj; prop = subject
    if not ans and dobject and subject:
        properties = find_matches_prop(subject)
        entities = find_matches_ent(dobject)
        ans = find_answer(properties, entities)
    # ent = dobj; prop = predicate
    if not ans and dobject and predicate:
        properties = find_matches_prop(predicate)
        entities = find_matches_ent(dobject)
        ans = find_answer(properties, entities)
    # ent = pobject; prop = subject
    if not ans and pobject and subject:
        entities = find_matches_ent(pobject)
        properties = find_matches_prop(subject)
        ans = find_answer(properties, entities)
    # ent = attr; prop = subject
    if not ans and attr and subject:
        properties = find_matches_prop(subject)
        entities = find_matches_ent(attr)
        ans = find_answer(properties, entities)
    # ent = subject; prop = pcomp
    if not ans and subject and pcomp:
        properties = find_matches_prop(pcomp)
        entities = find_matches_ent(subject)
        ans = find_answer(properties, entities)
    # ent = attr; prop = pcomp
    if not ans and attr and pcomp:
        properties = find_matches_prop(pcomp)
        entities = find_matches_ent(attr)
        ans = find_answer(properties, entities)
    # ent = labeled; prop = apposition
    if not ans and labeled and appos:
        properties = find_matches_prop(appos)
        entities = find_matches_ent(labeled)
        ans = find_answer(properties, entities)
    # ent = appos; prop = predicate
    if not ans and appos and predicate:
        properties = find_matches_prop(predicate)
        entities = find_matches_ent(appos)
        ans = find_answer(properties, entities)
    # ent = predicate; prop = subject
    if not ans and subject and predicate:
        properties = find_matches_prop(subject)
        entities = find_matches_ent(predicate)
        ans = find_answer(properties, entities)
    # ent = subject; prop = pobject
    if not ans and subject and pobject:
        properties = find_matches_prop(pobject)
        entities = find_matches_ent(subject)
        ans = find_answer(properties, entities)
    # ent = labeled; prop = dobject
    if not ans and dobject and labeled:
        entities = find_matches_ent(labeled)
        properties = find_matches_prop(dobject)
        ans = find_answer(properties, entities)
    # ent = subject; prop = predicate
    if not ans and subject and predicate:
        entities = find_matches_ent(subject)
        properties = find_matches_prop(predicate)
        ans = find_answer(properties, entities)
    # ent = labeled; prop = oprd
    if not ans and labeled and oprd:
        entities = find_matches_ent(labeled)
        properties = find_matches_prop(oprd)
        ans = find_answer(properties, entities)

    if ans:
        print(str(' '.join(ans)))
        return 1
    return 0
