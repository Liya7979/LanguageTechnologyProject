import requests
import spacy

input_parser = {
    'band members': 'has part',
    'members': 'has part',
    'real name': 'birth name',
    'born': 'birth',
    'wrote': 'librettist',
    'city': 'birth place',
    'kids': 'child',
    'child': 'number of children',
    'country': 'country of origin',
    'albums': 'discography',
    'soundtrack': 'soundtrack album'
}
entity_match = {
    'Q116': 'Q15862'
}
names = {'Jay-Z', 'Maroon 5', '50 Cent', 'Little Big', 'Black Pink', 'Beyoncé', 'Frozen'}
is_count = 1
is_soundtrack = 0
is_starting_date = 0
is_discography = 0
nlp = spacy.load('en_core_web_sm')


def answer_count_question(question):
    params = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}
    p = extract_object(question, params)
    q = extract_subject(question, params)
    q = check_for_special(question, q)
    p = check_for_special(question, p)
    params['type'] = 'property'
    if len(p) == 0 or len(q) == 0:
        return 0
    flag_to_break = 0
    flag = 0
    for i in q:
        if flag_to_break == 1:
            break
        for j in p:
            if i != j:
                query = create_and_fire_query(j, i, question)
                if query is not None:
                    flag = print_answer(query)
                    if flag == 1:
                        flag_to_break = 1
                        break

    if flag == 0:
        return 0
    else:
        return 1


def check_for_special(question, segm):
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(question)
    for i in doc:
        if i.text in input_parser:
            res = input_parser[i.text]
            segm.append(res)
    for i in segm:
        if i == 'discography':
            global is_discography
            is_discography = 1
        if i in input_parser:
            if i == 'child' or i == 'kid':
                global is_count
                is_count = 1
            elif i == 'soundtrack':
                global is_soundtrack
                is_soundtrack = 1
            segm.append(input_parser[i])
            segm.remove(i)
    return segm


# finding the query in the database and printing the answer if it exists
def print_answer(query):
    # zero flag is returned when no answer was found
    flag = 0
    url = 'https://query.wikidata.org/sparql'
    ans = []
    try:
        data = requests.get(url, params={'query': query, 'format': 'json'}).json()
        if data['results']['bindings'] is not None:
            for item in data['results']['bindings']:
                for var in item:
                    if item[var]['value'] is "0":
                        return 0
                    flag = 1
                    ans.append(item[var]['value'])
    except:
        return 0
    if len(ans) > 1:
        print("\t", len(ans))
    else:
        print("\t", ans[0])

    return flag


def create_query(prop, entity, question):
    date = extract_date(question)
    if len(date) == 1:
        query = 'SELECT (COUNT(?answer) AS ?answerLabel) ' \
                'WHERE {' \
                'wd:%s p:%s ?answer.' \
                '?answer pq:P580 ?start.' \
                'FILTER (?start <= "%s-12-31T00:00:00Z"^^xsd:dateTime)' \
                'SERVICE wikibase:label {' \
                'bd:serviceParam wikibase:language "en" .} ' \
                '}' % (entity, prop, date[0])
    elif len(date) == 2:
        query = 'SELECT (COUNT(?answer) AS (?answerLabel)) ' \
                'WHERE {' \
                'wd:%s p:%s ?answer.' \
                '?answer pq:P580 ?start.' \
                'FILTER (?start >= "%s-01-01T00:00:00Z"^^xsd:dateTime && ?start <= "%s-01-01T00:00:00Z"^^xsd:dateTime)' \
                'SERVICE wikibase:label {' \
                'bd:serviceParam wikibase:language "en" .} ' \
                '}' % (entity, prop, date[0], date[1])
    elif is_count != 1:
        query = 'SELECT DISTINCT ?answerLabel ' \
                'WHERE{' \
                ' wd:%s wdt:%s ?answer. ' \
                'SERVICE wikibase:label{' \
                ' bd:serviceParam wikibase:language "en".}' \
                '}' % (entity, prop)
    elif is_count == 1 and is_soundtrack != 1 and is_discography != 1:
        query = 'SELECT (COUNT(?number) AS ?numberLabel) ' \
                'WHERE{' \
                'wd:%s wdt:%s ?number.' \
                'SERVICE wikibase:label {' \
                ' bd:serviceParam wikibase:language "en" . }' \
                '}' % (entity, prop)
    elif is_soundtrack == 1 and is_count == 1:
        query = 'SELECT DISTINCT (COUNT(?answer) AS ?answerLabel) ' \
                'WHERE{' \
                ' wd:%s wdt:%s ?soundtrack. ' \
                ' ?soundtrack wdt:P658 ?answer.' \
                'SERVICE wikibase:label{' \
                ' bd:serviceParam wikibase:language "en".}' \
                '}' % (entity, prop)
    elif is_discography == 1 and is_count == 1:
        query = 'SELECT DISTINCT (COUNT(?answer) as ?answerLabel) ' \
                'WHERE{ ' \
                'wd:%s wdt:P358/wdt:P2354* ?album. ' \
                '?album wdt:P31 wd:Q59191021. ' \
                '?album wdt:P527 ?answer. ' \
                'SERVICE wikibase:label{ bd:serviceParam wikibase:language "en".}}' % (entity)
    return query


def create_and_fire_query(p, q, question):
    url = 'https://www.wikidata.org/w/api.php'
    params_q = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}
    params_p = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json', 'type': 'property'}
    params_q['search'] = q
    json = requests.get(url, params_q).json()
    for result in json['search']:
        q_id = format(result['id'])
        params_p['search'] = p
        json = requests.get(url, params_p).json()
        for result in json['search']:
            if p == 'number of children':
                global is_count
                is_count = 0
            elif p == 'child' or p == 'kid':
                is_count = 1
            p_id = format(result['id'])
            q_id = check_entity(q_id)
            query = create_query(p_id, q_id, question)
            return query


def check_entity(id):
    if id in entity_match:
        id = entity_match[id]
    return id


def extract_object(question, params):
    doc = nlp(question)
    segmented = []
    for token in doc.noun_chunks:
        chunk = nlp(token.text)
        lemmas = ''
        for i in chunk:
            if i.text != "How" and i.text != "many":
                if i.pos_ == 'NOUN' or i.pos_ == 'PROPN':
                    if i.text != 'cause' and i.text not in input_parser:
                        lemmas += i.lemma_
                    else:
                        lemmas += i.text
                elif i.pos_ != 'PART' and i.pos_ != 'VERB':
                    lemmas += i.text
                lemmas += ' '
        params['search'] = lemmas.strip()
        if token.root.dep_ == 'nsubj' or token.root.dep_ == 'nsubjpass' or token.root.dep_ == 'dobj':
            segmented.append(params['search'])
    for i in segmented:
        if i == '':
            segmented.remove(i)
    return list(filter(None.__ne__, segmented))


def extract_date(question):
    doc = nlp(question)
    additional = []
    for token in doc.ents:
        if token.label_ == "DATE":
            for t in token:
                if t.pos_ == 'NUM':
                    additional.append(t)
    return additional


def extract_subject(question, params):
    doc = nlp(question)
    segmented = []
    for ent in doc.ents:
        segmented.append(ent.text)
    for name in names:
        if name in question:
            segmented.append(name)
    for token in doc.noun_chunks:
        chunk = nlp(token.text)
        lemmas = ''
        for i in chunk:
            if chunk.text in names:
                segmented.insert(0, chunk.text)
                break
            elif i.text in names:
                segmented.insert(0, i.text)
            elif i.pos_ == 'NOUN':
                if i.pos_ == 'PROPN' or i.text[0].isupper():
                    lemmas += str(i)
                else:

                    lemmas += i.text
            lemmas += ' '
        params['search'] = lemmas.strip()
        segmented.append(params['search'])
    for i in segmented:
        if i == '':
            segmented.remove(i)
    return list(filter(None.__ne__, segmented))
