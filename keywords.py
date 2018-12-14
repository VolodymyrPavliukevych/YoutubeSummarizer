"""
Graph-based ranking model for text processing
Keyword and sentence extraction.

"""

import itertools
import nltk
import networkx as nx

def filter_for_tags(tagged, tags=['NN', 'JJ', 'NNP']):
    "Apply syntactic filters based on POS tags"
    return [item for item in tagged if item[1] in tags]

def do_normalize(tagged):
    "Normalize tags"
    return [(item[0].replace('.', ''), item[1]) for item in tagged]

def unique_everseen(iterable):
    "List unique elements, preserving order. Remember all elements ever seen."
    seen = set()
    for i in iterable:
        if not i in seen:
            seen.add(i)
    return seen

def levenshtein_distance(first_string, second_string):
    "Function to find the Levenshtein distance between two words/sentences"
    if len(first_string) > len(second_string):
        first_string, second_string = second_string, first_string
    distances = range(len(first_string) + 1)
    for index2, char2 in enumerate(second_string):
        new_distances = [index2 + 1]
        for index1, char1 in enumerate(first_string):
            if char1 == char2:
                new_distances.append(distances[index1])
            else:
                new_distances.append(1 + min((distances[index1], distances[index1+1], new_distances[-1])))
        distances = new_distances
    return distances[-1]

def build_graph(nodes):
    "nodes - list of hashables that represents the nodes of the graph"
    graph = nx.Graph() #initialize an undirected graph
    graph.add_nodes_from(nodes)
    node_pairs = list(itertools.combinations(nodes, 2))

    #add edges to the graph (weighted by Levenshtein distance)
    for pair in node_pairs:
        first_string = pair[0]
        second_string = pair[1]
        distance = levenshtein_distance(first_string, second_string)
        graph.add_edge(first_string, second_string, weight=distance)

    return graph

def extract_keyphrases(text):
    "Tokenize the text using nltk"
    word_tokens = nltk.word_tokenize(text)

    #assign POS tags to the words in the text
    tagged = nltk.pos_tag(word_tokens)
    textlist = [x[0] for x in tagged]

    tagged = filter_for_tags(tagged)
    tagged = do_normalize(tagged)

    unique_word_set = unique_everseen([x[0] for x in tagged])
    word_set_list = list(unique_word_set)

   #this will be used to determine adjacent words in order to construct keyphrases with two words
    graph = build_graph(word_set_list)

    #pageRank - initial value of 1.0, error tolerance of 0,0001, 
    calculated_page_rank = nx.pagerank(graph, weight='weight')

    #most important words in ascending order of importance
    keyphrases = sorted(calculated_page_rank, key=calculated_page_rank.get, reverse=True)

    #the number of keyphrases to return
    number_of_keyphrases = 20
    keyphrases = keyphrases[0:number_of_keyphrases+1]

    #take keyphrases with multiple words into consideration as done in the paper - if two words are adjacent in the text and are selected as keywords, join them
    #together
    modified_keyphrases = set([])
    dealt_with = set([]) #keeps track of individual keywords that have been joined to form a keyphrase
    i = 0
    j = 1
    while j < len(textlist):
        first_word = textlist[i]
        second_word = textlist[j]
        if first_word in keyphrases and second_word in keyphrases:
            keyphrase = first_word + ' ' + second_word
            modified_keyphrases.add(keyphrase)
            dealt_with.add(first_word)
            dealt_with.add(second_word)
        else:
            if first_word in keyphrases and first_word not in dealt_with:
                modified_keyphrases.add(first_word)

            #if this is the last word in the text, and it is a keyword,
            #it definitely has no chance of being a keyphrase at this point
            if j == len(textlist)-1 and second_word in keyphrases and second_word not in dealt_with:
                modified_keyphrases.add(second_word)

        i = i + 1
        j = j + 1

    return modified_keyphrases

def extract_summary_sentence(text):
    "Extract important sentences"
    sentence_tokens = nltk.word_tokenize(text)
    graph = build_graph(sentence_tokens)

    calculated_page_rank = nx.pagerank(graph, weight='weight')

    #most important sentences in ascending order of importance
    sentences = sorted(calculated_page_rank, key=calculated_page_rank.get, reverse=True)

    #return a 100 word summary
    summary = ' '.join(sentences)
    summary_words = summary.split()
    summary_words = summary_words[0:101]
    summary = ' '.join(summary_words)

    return summary
