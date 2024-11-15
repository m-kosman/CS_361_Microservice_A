import string
from datetime import datetime
from task_category_db import TaskCategoryDatabase, Categories
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('wordnet')


class TaskCategorization:
    """Represents a categorized task """
    def __init__(self, task_id, task):
        self._task_id = task_id
        self._task = task
        self._categories = None
        self._database = TaskCategoryDatabase()

        self.get_categories()
        self._processed_task = self.preprocess_string(self._task)
        self._category = self.find_category(self._processed_task)

    def get_category(self):
        """Getter for the category attribute"""
        return self._category

    def get_categories(self):
        """Initalizes a dictionary of categories to store # of database matches"""
        if self._categories is None:
            self._categories = {}
            # adds the categories that are in the database
            for category in Categories:
                self._categories[category.value] = 0

    def preprocess_string(self, task:str) -> list:
        """Handles preprocessing of the task for use in db queries"""
        task = task.lower()
        tokens = self.tokenize_string(task)
        lemmed_tokens = self.lemmatize_tokens(tokens)

        return lemmed_tokens

    def tokenize_string(self, task:str) -> list:
        """
        Separates the task string into individual words and removes
        punctuation/filler words

        :param task: a task to be categorized
        :return: a filtered list of the tokens
        """
        # creates the tokens
        tokens = nltk.word_tokenize(task)

        # gets sets of punctuation/filler words
        punctuation = set(string.punctuation)
        filler_words = set(stopwords.words("english"))

        # removed the punctuation and filler word tokens
        no_punctuation = [word for word in tokens if word not in punctuation]
        filtered_tokens = [word for word in no_punctuation if word not in filler_words]

        return filtered_tokens

    def lemmatize_tokens(self, tokens:list) -> list:
        """
        Stems the tokens using a lemmatizer.
        :param tokens: a list of filtered tokens
        :return: a list of lemmatized tokens
        """
        lemmatizer = WordNetLemmatizer()
        lemmed_tokens = [lemmatizer.lemmatize(word) for word in tokens]

        return lemmed_tokens

    def find_category(self, processed_tokens: list) -> str:
        """
        Receives a list of tokens from pre-processing and compares it to the database
        keywords.  Returns the category with the most matches to the task.
        :param processed_tokens: list of tokens from the client task
        :return: name of category with most matches
        """
        print(f"finding category {datetime.now()}")

        for key in self._categories:
            # gets the keywords
            cat_id = self._database.get_category_id(key)
            keywords = self._database.get_all_keywords_for_category(cat_id)

            matches = 0

            # checks for exact matches
            keyword_set = set(keywords)
            matches += len(set(processed_tokens) & keyword_set)

            # checks for tokens that partially match a phrase
            for keyword in keywords:
                for token in processed_tokens:
                    if keyword in processed_tokens:
                        matches += 1
                        break

            # stores the number of hits
            self._categories[key] = matches

        # gets category with the most hits
        category = max(self._categories, key=self._categories.get)

        # if the category has no hits then sets it to the default category personal
        if self._categories[category] == 0:
            category = "personal"

        print(f"returning category {datetime.now()}")
        return category
