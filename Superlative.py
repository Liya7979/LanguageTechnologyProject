import requests
import spacy

input_parser = {
    'oldest': 'has part',
    'youngest': 'has part',
    'selling': 'charted',
    'song': 'tracklist',
    'When': 'inception',
    'cousin': 'relative',
    'lowest': 'lowest note',
    'highest': 'highest note',
    'era': 'earliest date',
    'flutes': 'flute',
    'genre': 'music genre',
    'film': 'filmography'
}
entity_match = {
    'Q116': 'Q15862',
    'Q183': 'Q62565108'
}
names = {'Jay-Z', 'Maroon 5', '50 Cent', 'Little Big', 'Black Pink', 'Beyoncé', 'Frozen', 'The Upbeats'}
is_youngest = False
is_object = True
is_inception = False
is_released = False
is_general = False
is_streamed = False
is_award = False
nlp = spacy.load('en_core_web_sm')


def check_superlative(question):
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(question)
    superlative = False

    for i in doc:
        if (i.tag_ == "JJS" or i.tag_ == "RBS"):
            superlative = True
            break
    return superlative


def answer_superlative_question(question):
    global is_inception
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
                    # print(i, "---", j, "\n ", query, is_general, "<- general", is_released, "<- released", is_inception, "<- inception", is_youngest, "<- young", is_award, "<-award", is_object, "<- object", is_streamed, "<-stream")
                    flag = print_answer(query)
                    if flag == 1:
                        flag_to_break = 1
                        break
    if flag == 0:
        return 0


def check_for_special(question, segm):
    global is_inception, is_released, is_streamed, is_general, is_award, is_youngest, is_object
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(question)
    for i in doc:
        if i.text in input_parser:
            res = input_parser[i.text]
            segm.append(res)
        if i.text == 'youngest' or i.text == 'recently':
            is_youngest = True
        if i.text == 'member' or i.text == 'Who':
            is_object = False
        if i.text == 'When':
            is_inception = True
        if i.text == 'released':
            is_released = True
        if i.text == 'streamed':
            is_streamed = True
    for i in segm:
        if i in input_parser:
            segm.append(input_parser[i])
            segm.remove(i)
        if is_inception is True and 'song' in question:
            segm = [value for value in segm if value != 'tracklist']
            if 'song' not in segm:
                segm.append('song')
        if 'first' not in question \
                and 'note' not in question \
                and 'era' not in question \
                and 'known' not in question:
            is_general = True
        if 'award' in question:
            is_award = True
    return segm


# finding the query in the database and printing the answer if it exists
def print_answer(query):
    # zero flag is returned when no answer was found
    flag = 0
    url = 'https://query.wikidata.org/sparql'
    try:
        data = requests.get(url, params={'query': query, 'format': 'json'}).json()
        for item in data['results']['bindings']:
            for var in item:
                if item[var]['value'] is "0":
                    return 0
                flag = 1
                print(item[var]['value'])
                reinitialize_globals()
    except:
        return 0
    return flag


def reinitialize_globals():
    global is_streamed, is_general, is_released, is_object, is_inception, is_youngest
    is_youngest = False
    is_object = True
    is_inception = False
    is_released = False
    is_general = False
    is_streamed = False


def create_query(prop, entity):
    global is_inception
    additional_property = 'P577' if is_object is True else 'P569'
    order = 'DESC(?band)' if is_youngest is True else '?band'
    if is_streamed is True:
        query = 'SELECT ?songLabel ' \
                'WHERE{ ?song wdt:P31 wd:Q193977. ' \
                '?song wdt:P5436 ?viewers. ' \
                'SERVICE wikibase:label {' \
                ' bd:serviceParam wikibase:language "en" . ' \
                '} ' \
                '} ' \
                'ORDER BY DESC(?viewers) ' \
                'LIMIT 1'
    elif is_award is True:
        query = 'SELECT DISTINCT ?answerLabel ' \
                'WHERE{' \
                'wd:%s p:P166 ?name. ' \
                '?name ps:P166 ?answer. ' \
                '?name pq:P585 ?band. ' \
                'SERVICE wikibase:label { ' \
                'bd:serviceParam wikibase:language "en" . }}' \
                'ORDER BY %s ' \
                'LIMIT 1' % (entity, order)
    elif is_inception is True and is_released is False:
        query = 'SELECT (YEAR(?date) AS ?year) ' \
                'WHERE { ' \
                '?answer wdt:P31 wd:%s. ' \
                '?answer wdt:P571 ?date. ' \
                'FILTER (!isBlank(?date)) ' \
                'SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . } } ' \
                'ORDER BY ?date ' \
                'LIMIT 1' % entity
    elif is_released is False and is_general is True:
        query = '''SELECT ?nameLabel 
                WHERE{
                wd:%s wdt:%s ?name.
                ?name wdt:%s ?band.
                SERVICE wikibase:label { 
                  bd:serviceParam wikibase:language "en" . 
                }
                }
                ORDER BY %s
                LIMIT 1''' % (entity, prop, additional_property, order)
    elif is_released is True:
        query = '''SELECT ?nameLabel 
                        WHERE{
                        wd:%s wdt:%s ?name.
                        SERVICE wikibase:label { 
                          bd:serviceParam wikibase:language "en" . 
                        }} ORDER BY ?name
                        LIMIT 1
                        
                        ''' % (entity, additional_property)
    else:
        query = '''SELECT ?nameLabel 
                                WHERE{
                                wd:%s wdt:%s ?name.
                                SERVICE wikibase:label { 
                                  bd:serviceParam wikibase:language "en" . 
                                }
                                }
                                ''' % (entity, prop)
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
            if p == 'youngest':
                global is_youngest
                is_youngest = True
            p_id = format(result['id'])
            q_id = check_entity(q_id)
            query = create_query(p_id, q_id)
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
            if i.text != "Which" and i.text != "Who" and i.text != "What":
                if i.pos_ == 'NOUN' or i.pos_ == 'PROPN':
                    if i.text != 'cause' and i.text not in input_parser:
                        lemmas += i.lemma_
                    else:
                        lemmas += i.text

                lemmas += ' '
        params['search'] = lemmas.strip()
        if token.root.dep_ == 'nsubj' or token.root.dep_ == 'nsubjpass' or token.root.dep_ == 'dobj':
            segmented.append(params['search'])
    for i in segmented:
        if i == '':
            segmented.remove(i)
    return list(filter(None.__ne__, segmented))


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
