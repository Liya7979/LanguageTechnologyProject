import requests
import sys
import spacy
from Dueto import create_and_fire_queryDueto
#from How import create_and_fire_query_How
from Whatextra import create_and_fire_queryWhatextra
from WhatWhoOfDescription import create_and_fire_queryWhatWhoOfD
from WhenWhere import create_and_fire_query_WhenWhere
from WhoExtra import create_and_fire_queryWhoextra
from Whowhatpocession import create_and_fire_queryWhowhatpocession
from YesorNoBe import create_and_fire_queryYesorNoBe
from YesorNoDo import create_and_fire_queryYesorNoDo
from Howmany import answer_count_question
from Which import create_and_fire_query_adv
from Superlative import answer_superlative_question


def check_type(string):
    answer = 0
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(string)
    if string:
        Keyword = string.split()[0]
        if ("Are" in Keyword or "Is" in Keyword or "are" in Keyword or "is" in Keyword or "Was" in Keyword
            or "was" in Keyword or "Were" in Keyword or "were" in Keyword) and answer == 0:
            answer = create_and_fire_queryYesorNoBe(string)

        if ("Do" in Keyword or "Did" in Keyword or "Does" in Keyword or "do" in Keyword or "did" in Keyword
            or "does" in Keyword) and answer == 0:
            answer = create_and_fire_queryYesorNoDo(string)

        if ("Due" in Keyword or "due" in Keyword) and answer == 0:
            answer = create_and_fire_queryDueto(string)

        if ("Who" in string or "What" in string or "who" in string or "what" in string) and answer == 0:
            if "'s" in string or "s'" in string or "’s" in string:
                answer = create_and_fire_queryWhowhatpocession(string)
            if answer == 0 and ("Who" in string or "who" in string):
                answer = create_and_fire_queryWhoextra(string)
            if answer == 0 and ("What" in string or "what" in string):
                answer = create_and_fire_queryWhatextra(string)

            if answer == 0:
                answer = create_and_fire_queryWhatWhoOfD(string)

        if ("When" in string or "Where" in string or "when" in string or "where" in string) and answer == 0:
            answer = create_and_fire_query_WhenWhere(string)

        #if ("How" in string or "how" in string) and answer == 0:
        #    answer = create_and_fire_query_How(string)

        if ("How many" or "how many" in string) and answer == 0:
            answer = answer_count_question(string)

        superlative = False
        for i in doc:
            if i.tag_ == "JJS" or i.tag_ == "RBS" or i.tag_ == "JJ":
                superlative = True
                break
        if superlative is True:
            answer = answer_superlative_question(string)

        if answer == 0:
            answer = create_and_fire_query_adv(string)

    return answer

def main(argv):
    f = open("questions.txt", "r+")
   # for line in sys.stdin:
    for line in f:
        line = line.rstrip()  # removes newline
        print(line)
        answer = check_type(line)
        if answer == 0:
            print("No answer available")

    f.close()
if __name__ == "__main__":
    main(sys.argv)
