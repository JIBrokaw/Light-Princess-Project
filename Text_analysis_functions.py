from collections import Counter
from collections import defaultdict
from random import choice


class Text_Analysis():
    def __init__(self, file):
        #Get raw string
        self.filename = file
        with open(self.filename,"r") as file:
            text = file.read()
        #Useful variables
        self.__text_words = text.split()
        frequency_dict = Counter()
        self.__chapter_dicts = []
        self.__chapter_indices = []
        self.__next_words = defaultdict(list)
        self.__next_next_words = defaultdict(list)
        self.__sentence_order = []
        self.__sentence_trie = dict()

        #Make stop words list
        self.__stop_words = set()
        with open('stop_words_long.txt') as file:
            for line in file:
                self.__stop_words.add(line.strip('\n'))

        #Read through whole list of words and set up dictionaries
        prev_prev_word = None
        prev_word = None
        prev_dict = self.__sentence_trie
        cur_chapter_dict = None
        place_in_sentence = 0
        for i in range(len(self.__text_words)):
            word = self.__text_words[i]
            clean_word = word.strip(',.!?;()-\'\"').lower()

            #next words dictionary
            if prev_word:
                self.__next_words[prev_word].append(clean_word)
                if prev_prev_word:
                    self.__next_next_words[prev_prev_word].append(clean_word)
            prev_prev_word = prev_word
            prev_word = clean_word

            #place in sentence tracker (for bestQuoteGenerator())
            if len(self.__sentence_order) == place_in_sentence:
                self.__sentence_order.append(set())
            self.__sentence_order[place_in_sentence].add(clean_word)
            place_in_sentence += 1

            #predictive trie
            if clean_word not in prev_dict.keys():
                prev_dict[clean_word] = dict()
            prev_dict = prev_dict[clean_word]

            #At the end of a sentence
            punctuation = word.strip('\'")')[-1]
            if punctuation == '.' or punctuation == '!' or punctuation == '?':
                #next words dictionary
                self.__next_next_words[prev_prev_word].append(punctuation)
                self.__next_words[prev_word].append(punctuation)
                prev_word = None
                prev_prev_word = None
                #place in sentence tracker
                place_in_sentence = 0
                #predictive trie
                if punctuation not in prev_dict:
                    prev_dict[punctuation] = None
                prev_dict = self.__sentence_trie

            #notice chapter breaks
            if word == "CHAPTER":
                cur_chapter_dict = Counter()
                self.__chapter_dicts.append(cur_chapter_dict)
                self.__chapter_indices.append(i+2)
            #make the frequency dictionaries
            else:
                frequency_dict[clean_word] += 1
                cur_chapter_dict[clean_word] += 1
        self.__chapter_indices.append(len(self.__text_words))

        self.__sorted_frequency_dict = frequency_dict.most_common()


    def getTotalNumberOfWords(self): #As project specifications
        return(len(self.__text_words))

    def getTotalUniqueWords(self): #As project specifications
        return(len(self.__sorted_frequency_dict))

    def get20MostFrequentWords(self, num = 20): #As project specifications
        return(self.__sorted_frequency_dict[:20])

    def get20MostInterestingFrequentWords(self, num = 20): #As project specifications
        most_freq_list = []
        i = 0
        while len(most_freq_list) < num:
            if self.__sorted_frequency_dict[i][0] not in self.__stop_words:
                most_freq_list.append(self.__sorted_frequency_dict[i])
            i += 1
        return most_freq_list

    def get20LeastFrequentWords(self, num = 20): #As project specifications. In practice, retrieves the uncommon words nearest the end of the book first.
        least_freq_list = []
        for i in range(len(self.__sorted_frequency_dict)-num, len(self.__sorted_frequency_dict)):
            least_freq_list.append(self.__sorted_frequency_dict[i])
        return least_freq_list

    def getFrequencyOfWord(self, word): #Also accepts partial words as in database searches. E.g. cry* finds both "crying" and "cry" and returns the total per chapter.
        list_to_return = []
        for dict in self.__chapter_dicts:
            if not word.endswith('*'):
                #Full word, as in project specifications
                list_to_return.append(dict[word.lower()])
            else:
                #Partial word lookups
                list_to_return.append(0)
                for key in dict.keys():
                    if key.startswith(word.lower()[:len(word)-1]):
                        list_to_return[-1] += dict[key]
        return list_to_return

    #Private method for finding a sublist of words within a list of words, used in getChapterQuoteAppears(). Returns either the full sentence in which the quote appeared, or False if not found.
    def __find_sublist(self,sub,main):
        j = 0
        start_index = 0
        for i in range(len(main)-len(sub)):
            #Walk through the chapter word by word.
            if main[i].lower().strip(',.!?;-()\'\"') == sub[j].lower().strip(',.!?;-()\'\"'):
                j += 1
            else:
                if main[i].lower().strip(',.!?;-()\'\"') == sub[0].lower().strip(',.!?;-()\'\"'):
                    j = 1
                else:
                    j = 0
            if main[i].endswith('.') or main[i].endswith('?') or main[i].endswith('!'):
                #If the sentence has ended and the quote is not found, reset the start of sentence marker.
                if j != len(sub) and not (sub[j].endswith('.') or sub[j].endswith('?') or sub[j].endswith('!')):
                    start_index = i + 1
            if j == len(sub):
                #If the full quote is found, read to the end of the sentence, then return the whole sentence.
                while not (main[i].endswith('.') or main[i].endswith('?') or main[i].endswith('!')):
                    i += 1
                return ' '.join(main[start_index:i+1])
        return False

    def getChapterQuoteAppears(self, quote): #Also prints the full sentence in which the quote can be found.
        quote_words = quote.split()
        #First check that all the words are in the chapter
        for chapter in range(len(self.__chapter_dicts)):
            correct = True
            for word in quote_words:
                if word.strip(',.!?;-()\'\"').lower() not in self.__chapter_dicts[chapter]:
                    correct = False
                    break
            #if so, scan the whole chapter to find the words in sequence
            if correct == True:
                quote_sentence = self.__find_sublist(quote_words,self.__text_words[self.__chapter_indices[chapter]:self.__chapter_indices[chapter+1]-2])
                if quote_sentence:
                    return '"' + quote_sentence + '" is found in Chapter ' + str(chapter + 1) + '.'
        return "Sorry, quote not found"

    def findClosestMatchingQuote(self,quote): #Also prints the full sentence in which the real quote can be found.
        quote_words = quote.split()
        quote_to_return = ''
        #clean the quote
        clean_quote_words = []
        for word in quote_words:
            word = word.strip(',.!?;-()\'\"').lower()
            if word not in self.__stop_words:
                clean_quote_words.append(word)
        if len(clean_quote_words) == 0: #If all the words were so general they got deleted, the quote can't be found and probably isn't worth finding.
            return "Sorry, please try a more specific quote."
        #Check if all the relevant words are in the chapter
        for chapter in range(len(self.__chapter_dicts)):
            correct = True
            for word in clean_quote_words:
                if word not in self.__chapter_dicts[chapter]:
                    correct = False
                    break
            if correct == True:
                #print the real quote
                start_index = self.__chapter_indices[chapter]
                seeking_words = set(clean_quote_words)
                for i in range(self.__chapter_indices[chapter],self.__chapter_indices[chapter+1]-2):
                    word = self.__text_words[i]
                    clean_word = word.strip(',.!?;-()\'\"').lower()
                    if clean_word in seeking_words:
                        seeking_words.remove(clean_word)
                    if word.endswith('.') or word.endswith('?') or word.endswith('!'):
                        if len(seeking_words) == 0:
                            quote_to_return = ' '.join(i for i in self.__text_words[start_index:i+1])
                            break
                        else:
                            start_index = i+1
                            seeking_words = seeking_words.union(clean_quote_words)
                if len(seeking_words) == 0:
                    return 'The actual quote is "' + quote_to_return + '", and is found in Chapter ' + str(chapter + 1)
        return "Sorry, quote not found"

    def generateSentence(self): #Stops at end of sentence rather than 20th word.
        sentence_list = []
        word = 'the'
        while word != '.' and word != '?' and word != '!':
            sentence_list.append(word)
            word = choice(self.__next_words[word])
        if len(sentence_list) < 3:
            #If the sentence is only 2 words long, it probably isn't a sentence, so try again. I kept getting sentences like "The princess.""
            return self.generateSentence()
        sentence_list[0] = 'The'
        return " ".join(sentence_list) + word

    #Bonus method in an attempt to generate a more meaningful sentence. It works the same way as generateSentence(), but looks two words back rather than just one. Does it actually work better ... sort of?
    def generateBetterSentence(self):
        sentence_list = []
        word = 'the'
        while word != '.' and word != '?' and word != '!':
            next_word = choice(self.__next_words[word])
            while len(sentence_list) > 1 and next_word not in self.__next_next_words[sentence_list[-1]]:
                next_word = choice(self.__next_words[word])
            sentence_list.append(word)
            word = next_word
        if len(sentence_list) < 3:
            return self.generateBetterSentence()
        sentence_list[0] = 'The'
        return " ".join(sentence_list) + word

    def generateBestSentence(self):
        sentence_list = []
        word = 'the'
        word_counter = 1
        while word != '.' and word != '?' and word != '!':
            next_word = choice(self.__next_words[word])
            while len(sentence_list) > 1 and next_word not in self.__next_next_words[sentence_list[-1]] and (next_word != '.' and next_word != "?" and next_word != '!') and next_word not in self.__sentence_order[word_counter]:
                next_word = choice(self.__next_words[word])
            sentence_list.append(word)
            word_counter += 1
            word = next_word
        if len(sentence_list) < 3:
            return self.generateBestSentence()
        sentence_list[0] = 'The'
        return " ".join(sentence_list) + word



    def getAutocompleteSentence(self, quote): #As in project specifications.
        quote_words = quote.split()
        cur_dict = self.__sentence_trie
        #Walk down the trie as far as the end of the given quote-fragment.
        for word in quote_words:
            word = word.strip(',.!?;-()\'\"').lower()
            if word in cur_dict.keys():
                cur_dict = cur_dict[word]
            else:
                return "Sorry, this quote is not found"

        def dfs_trie(current_word): #Private recursive method for a depth-first-search of the trie.
            list_of_lists = []
            if current_word is None:
                return [[]]
            for word in current_word.keys():
                returned_list = dfs_trie(current_word[word])
                for list in returned_list:
                    list_of_lists.append(list)
                    list_of_lists[-1].append(word)
            return list_of_lists

        #Generate all remaining sentences stored in the trie from that point.
        sentence_endings = dfs_trie(cur_dict)
        sentences = []
        for list in sentence_endings:
            for i in range(len(quote_words)-1,-1,-1):
                list.append(quote_words[i])
            list.reverse()
            sentences.append(" ".join(word for word in list[:len(list)-1]) + ".")
        return sentences


#One-pass analysis of the chosen text, as a demonstration.
def analysis_output(filename):
    BookAnalysis = Text_Analysis(filename)
    BookTitle = filename[:len(filename)-4]
    print('\nBasic information:')
    print('\tTotal Word Count of ' + BookTitle + ':', BookAnalysis.getTotalNumberOfWords())
    print('\tUnique Words in ' + BookTitle + ':', BookAnalysis.getTotalUniqueWords())
    print()
    print('\tMost common words in ' + BookTitle + ':',BookAnalysis.get20MostFrequentWords())
    print('\tMost common interesting words in ' + BookTitle + ':', BookAnalysis.get20MostInterestingFrequentWords())
    print('\tLeast frequent Words in ' + BookTitle + ':', BookAnalysis.get20LeastFrequentWords())
    print()
    frequent_word = input('What word would you like to check the per-chapter frequency of? ')
    print('Frequency of ' + frequent_word + ' in ' + BookTitle + ':',BookAnalysis.getFrequencyOfWord(frequent_word))
    print()
    quote = input('What quote would you like to look up the chapter of? ')
    answer = BookAnalysis.getChapterQuoteAppears(quote)
    if answer == "Sorry, quote not found":
        answer = BookAnalysis.findClosestMatchingQuote(quote)
    print(str(answer))
    print()
    sentence = input('What sentence would you like to complete? ')
    print('The sentences in ' + BookTitle + ' starting with those words are: ', BookAnalysis.getAutocompleteSentence(sentence))
    print()
    number_to_generate = int(input('How many random sentences would you like to generate with each method? '))
    for i in range(number_to_generate):
        print('Randomly generated sentence:', BookAnalysis.generateSentence())
    print()
    for i in range(number_to_generate):
        print('Better Randomly generated sentence:', BookAnalysis.generateBetterSentence())

#Menu-oriented analysis of the chosen text, for more efficient research
def analysis_control(filename):
    BookAnalysis = Text_Analysis(filename)
    BookTitle = filename[:len(filename)-4]
    while True:
        option = input('What would you like to analyze about ' + BookTitle + '? \n\tFrequency\n\tQuote\n\tGenerate\n')
        #Frequency functions
        if 'frequency' in option.lower():
            print(' What sort of frequency are you looking for?')
            option = input('\tMost frequent \n\tLeast frequent \n\tMost frequent interesting \n\tFrequency by word \n')
            if 'interesting' in option.lower():
                if option.split()[-1].isdigit():
                    print('\tMost frequent interesting words in ' + BookTitle + ':', BookAnalysis.get20MostInterestingFrequentWords(int(option.split()[-1])))
                else:
                    print('\tMost frequent interesting words in ' + BookTitle + ':', BookAnalysis.get20MostInterestingFrequentWords())
            elif 'most' in option.lower():
                if option.split()[-1].isdigit():
                    print('\tMost frequent words in ' + BookTitle + ':', BookAnalysis.get20MostInterestingFrequentWords(int(option.split()[-1])))
                else:
                    print('\tMost frequent words in ' + BookTitle + ':', BookAnalysis.get20MostInterestingFrequentWords())
            elif 'least' in option.lower():
                if option.split()[-1].isdigit():
                    print('\tLeast frequent words in ' + BookTitle + ':', BookAnalysis.get20MostInterestingFrequentWords(int(option.split()[-1])))
                else:
                    print('\tLeast frequent words in ' + BookTitle + ':', BookAnalysis.get20MostInterestingFrequentWords())
            else:
                while True:
                    option = input('What word would you like to look for? ')
                    if len(option.split()) > 1:
                        print('Sorry, only one word at a time, please.')
                    else:
                        if 'back' in option.lower() or 'exit' in option.lower():
                            break
                        print('Frequency of ' + option + ' in ' + BookTitle + ':',BookAnalysis.getFrequencyOfWord(option))

        elif 'find' in option.lower() or 'quote' in option.lower():
            quote = input('What quote would you like to find? ')
            answer = BookAnalysis.getChapterQuoteAppears(quote)
            if answer == "Sorry, quote not found":
                answer = BookAnalysis.findClosestMatchingQuote(quote)
            print(str(answer))

        elif 'generate' in option.lower() or 'sentence' in option.lower():
            option = input('Would you like to generate real sentences from the book, or new ones? ')
            if 'new' in option.lower():
                while True:
                    number_to_generate = input('How many sentences would you like to generate? ')
                    if not number_to_generate.isdigit():
                        break
                    else:
                        number_to_generate = int(number_to_generate)
                    option = input('Which method would you like to use? 1, 2, or 3? ')
                    if '3' in option:
                        for i in range(number_to_generate):
                            print('Best Randomly generated sentence:', BookAnalysis.generateBestSentence())
                    elif '2' in option:
                        for i in range(number_to_generate):
                            print('Better Randomly generated sentence:', BookAnalysis.generateBetterSentence())
                    else:
                        for i in range(number_to_generate):
                            print('Randomly generated sentence:', BookAnalysis.generateSentence())
                    print()
            else:
                sentence = input('What sentence would you like to complete? ')
                print('The sentences in ' + BookTitle + ' starting with those words are: ', BookAnalysis.getAutocompleteSentence(sentence))

        elif 'exit' in option.lower() or 'stop' in option.lower():
            break

        else:
            print('Sorry, that input is not recognized. Please try again.')

        print()


if __name__ == "__main__":
    mode = input('What analysis mode are you in? Research or demo? ')
    possible_books = ['The Light Princess']
    book_choice = 'princess' #input('Which book would you like to analyze? \t' + "\t".join(book for book in possible_books) + '\n')
    if 'princess' in book_choice.lower() or 'light' in book_choice.lower():
        if 'demo' in mode.lower():
            analysis_output('Light_Princess.txt')
        else:
            analysis_control('Light_Princess.txt')
    # elif 'five' in book_choice.lower() or 'children' in book_choice.lower():
    #     if 'demo' in mode.lower():
    #         analysis_output('Five_Children_and_It.txt')
    #     else:
    #         analysis_control('Five_Children_and_It.txt')
    # elif 'call' in book_choice.lower() or 'wild' in book_choice.lower():
    #     if 'demo' in mode.lower():
    #         analysis_output('Call_of_the_Wild.txt')
    #     else:
    #         analysis_control('Call_of_the_Wild.txt')
