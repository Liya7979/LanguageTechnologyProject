import requests
import sys
import spacy
from Dueto import create_and_fire_queryDueto
from How import create_and_fire_query_How
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
from Superlative import check_superlative
from list import create_and_fire_query_dobj
from filter import create_and_fire_query_filter

def check_type(string):
    answer = 0
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(string)
    if string:
        Keyword = string.split()[0]

        if ("after" in string or "before" in string or "between" in string) and answer == 0:
            answer = create_and_fire_query_filter(string)
            if answer == 1:
                print("filter")

        if ("Name" in Keyword or "name" in Keyword or "List" in Keyword or "list" in Keyword) and answer == 0:
            answer = create_and_fire_query_dobj(string)
            if answer == 1:
                print("list")

        if ("Are" in Keyword or "Is" in Keyword or "are" in Keyword or "is" in Keyword or "Was" in Keyword
            or "was" in Keyword or "Were" in Keyword or "were" in Keyword) and answer == 0:
            answer = create_and_fire_queryYesorNoBe(string)
            if answer == 1:
                print("Yes/No")

        if ("Do" in Keyword or "Did" in Keyword or "Does" in Keyword or "do" in Keyword or "did" in Keyword
            or "does" in Keyword) and answer == 0:
            answer = create_and_fire_queryYesorNoDo(string)
            if answer == 1:
                print("Yes/No")

        if ("Due" in Keyword or "due" in Keyword) and answer == 0:
            answer = create_and_fire_queryDueto(string)
            if answer == 1:
                print("Due to")

        if ("Who" in string or "What" in string or "who" in string or "what" in string) and answer == 0:
            if "'s" in string or "s'" in string or "’s" in string:
                answer = create_and_fire_queryWhowhatpocession(string)
                if answer == 1:
                    print("Whoprocession")
            if answer == 0 and ("Who" in string or "who" in string):
                answer = create_and_fire_queryWhoextra(string)
                if answer == 1:
                    print("Whoextra")
            if answer == 0 and ("What" in string or "what" in string):
                answer = create_and_fire_queryWhatextra(string)
                if answer == 1:
                    print("Whatextra")

            if answer == 0:
                answer = create_and_fire_queryWhatWhoOfD(string)
                if answer == 1:
                    print("Whowhatdes")

        if ("When" in string or "Where" in string or "when" in string or "where" in string) and answer == 0:
            answer = create_and_fire_query_WhenWhere(string)
            if answer == 1:
                print("whenwhere")

        if ("How" in string or "how" in string) and answer == 0:
            answer = create_and_fire_query_How(string)
            if answer == 1:
              print("How")

        if ("How many" in string and answer is 0) or ("how many" in string and answer is 0):
            answer = answer_count_question(string)
            if answer == 1:
                print("howmany")

        if check_superlative(string) is True and answer is 0:
            answer = answer_superlative_question(string)
            if answer == 1:
                print("superlative")

        if answer == 0:
            answer = create_and_fire_query_adv(string)
            if answer == 1:
                print("Which")

    return answer

def main(argv):
    f = open("questions_liya.txt", "r+", encoding="utf-8")
    #for line in sys.stdin:
    for line in f:
        line = line.rstrip()  # removes newline
        print(line)
        try:
            answer = check_type(line)
        except Exception as e:
            print("Crashed: ", e)
        if answer == 0:
            print("No answer available")
    f.close()

if __name__ == "__main__":
    main(sys.argv)
