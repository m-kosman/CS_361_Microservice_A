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
    def __init__(self, task_id, task):
        self._task_id = task_id
        self._task = task
        self._categories = None
        self._database = TaskCategoryDatabase()

        self.get_categories()
        self._processed_task = self.preprocess_string(self._task)
        self._category = self.find_category(self._processed_task)

    def get_category(self):
        return self._category

    def get_categories(self):
        """initalizes dictionary of categories to store # of db matches """
        if self._categories is None:
            self._categories = {}
            for category in Categories:
                self._categories[category.value] = 0

    def preprocess_string(self, task):
        """handles preprocessing of the task for use in db queries"""
        task = task.lower()
        tokens = self.tokenize_string(task)
        lemmed_tokens = self.lemmatize_tokens(tokens)

        return lemmed_tokens

    def tokenize_string(self, task):
        """separates string into individual words and removes punctuation/filler words"""
        tokens = nltk.word_tokenize(task)
        punctuation = set(string.punctuation)
        filler_words = set(stopwords.words("english"))

        no_punctuation = [word for word in tokens if word not in punctuation]
        filtered_tokens = [word for word in no_punctuation if word not in filler_words]

        return filtered_tokens

    def lemmatize_tokens(self, tokens):
        """stems words using a lemmatizer"""
        lemmatizer = WordNetLemmatizer()
        lemmed_tokens = [lemmatizer.lemmatize(word) for word in tokens]
        return lemmed_tokens

    def find_category(self, processed_tokens):
        print(f"finding category {datetime.now()}")
        for key in self._categories:
            # gets the keywords
            cat_id = self._database.get_category_id(key)
            keywords = self._database.get_all_keywords_for_category(cat_id)

            # # preprocesses the keywords
            # processed_keywords = []
            # for keyword in keywords:
            #     result = self.preprocess_string(keyword)
            #     processed_keywords.extend(result)

            # checks for any matches
            matches = 0

            keyword_set = set(keywords)
            matches += len(set(processed_tokens) & keyword_set)

            for keyword in keywords:
                for token in processed_tokens:
                    if keyword in processed_tokens:
                        matches += 1
                        break

            self._categories[key] = matches
        # gets key with max value
        category = max(self._categories, key=self._categories.get)

        # if the key has a 0 value then sets it to the default category personal
        if self._categories[category] == 0:
            category = "personal"

        print(self._categories)
        print(category)
        print(f"returning category {datetime.now()}")
        return category


# task1 = 'Complete homework assignment'
# task2 = 'Prepare presentation slides'
# task3 = 'Grocery shopping for the week'
# task4 = 'Attend team meeting at 3 PM'
# task5 = 'Write blog post for the website'
# task6 = 'Call the doctor for an appointment'
# task7 = 'Clean and organize the workspace'
# task8 = 'Respond to work emails'
# task9 = 'Pick up dry cleaning'
# task10 = 'Walk the dog in the evening'
#
# categorizer = TaskCategorization(1, task7)



