from collections import defaultdict, namedtuple
from typing import List, Dict, Union


#  DEFAULTSTRUCTURE = 'AUTHOR;GENRE;TITLE;SERIES;SERNO;FILE;SIZE;LIBID;DEL;EXT;DATE;LANG;LIBRATE;KEYWORDS';
class Book(namedtuple("Book", "authors genres title series ser_no filename size lib_id deleted ext date lang librate keywords archive_filename")):
    @staticmethod
    def get_filed_num(name: str) -> Union[int, None]:
        if name not in Book._fields:
            return None
        return Book._fields.index(name)

    @property
    def uuid(self):
        return f'{self.filename}:{self.ser_no}:{self.lib_id}'

    @property
    def view_title(self):
        return f'{self.title} | {self.series} | {self.date}'

    @property
    def camelcase_authors(self):
        return [a.title() for a in self.authors]

    @property
    def dst_full_filename(self):
        return f'{" ".join(self.camelcase_authors)} - {self.title}'

    @property
    def dst_short_filename(self):
        return f'{self.authors[0].title()} - {self.title}'


class SimpleLib:
    def __init__(self):
        self.by_authors = defaultdict(list)
        self.by_genre = defaultdict(list)
        self.authors_letters = set()
        self.genres_letters = set()
        self.books = {}  # type: Dict[str, Book]

    def get_authors(self, pattern: str) -> List[str]:
        res = []
        for author in self.by_authors.keys():
            if pattern in author:
                res.append(author)
        return res

    def get_by_author(self, author: str) -> List[Book]:
        return self.by_authors.get(author)

    def get_by_genre(self, genre: str) -> List[Book]:
        res = []
        for key in self.by_genre:
            if genre in key:
                res.extend(self.by_genre[key])
        return res

    def _merge(self, data: Dict[str, Book], destination: Dict[str, Book]) -> None:
        for key, books in data.items():
            self.by_authors[key].extend(books)
            for book in books:
                self.books[f'{book.uuid}'] = book

    def merge_by_autors(self, data: Dict[str, Book]) -> None:
        self._merge(data, self.by_authors)
        for author in data.keys():
            self.authors_letters.add(author.lower()[0])

    def merge_by_genres(self, data: Dict[str, Book]) -> None:
        self._merge(data, self.by_genre)
        for genre in data.keys():
            self.genres_letters.add(genre.lower()[0])


LIBRARY = SimpleLib()
