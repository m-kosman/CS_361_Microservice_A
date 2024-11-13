import string

from nltk import SnowballStemmer

from task_category_db import TaskCategoryDatabase
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('wordnet')




class TaskCategorization:
    def __init__(self, task_id, task):
        self._task_id = task_id
        self._task = task

        self._processed_task = self.preprocess_string(self._task)
        self._category = self.find_category(self._processed_task)

    def preprocess_string(self, task):
        """handles preprocessing of the task for use in db queries"""
        task = task.lower()
        tokens = self.tokenize_string(task)
        lemmed_tokens = self.lemmatize_tokens(tokens)

        return lemmed_tokens

    def tokenize_string(self, task):
        """separates string into individual words and removes punctuation/filler words"""
        tokens = nltk.word_tokenize(task)
        print(tokens)
        punctuation = set(string.punctuation)
        filler_words = set(stopwords.words("english"))

        no_punctuation = [word for word in tokens if word not in punctuation]
        print(no_punctuation)
        filtered_tokens = [word for word in no_punctuation if word not in filler_words]
        print(filtered_tokens)

        return filtered_tokens

    def lemmatize_tokens(self, tokens):
        """stems words using a lemmatizer"""
        lemmatizer = WordNetLemmatizer()
        lemmed_tokens = [lemmatizer.lemmatize(word) for word in tokens]
        print(lemmed_tokens)
        return lemmed_tokens

    def find_category(self, processed_tokens):
        pass




