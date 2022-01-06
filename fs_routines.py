import re
import csv
import os

from zipfile import ZipFile
from collections import defaultdict
from os import path as os_path
from typing import Dict, List, Callable, Iterable

from memory_storage import LIBRARY, Book


INP_PAT = re.compile("^[df][t\\\.b]")
INPX_FIELD_DELIMITER = chr(4)
INPX_ITEM_DELIMITER = ':'
INPX_SUBITEM_DELIMITER = ','
ARCHIVE_EXT = 'zip'
BAD_DIR_CHARACTERS_PAT = re.compile(r'[\<\>:"/\\\|\?\*]')  # for regexp, so 'r' is needed
REPLACE_DIR_CHARACTER = '_'


def _make_list(value: str) -> List[str]:
    return [entity for entity in sorted(value.split(INPX_ITEM_DELIMITER)) if entity]


def _preprocess_row(row: List[str], archive_name: str) -> None:
    # !!! Change source list !!!
    # join authors name by space
    num = Book.get_filed_num('authors')
    row[num] = _make_list(row[num].replace(INPX_SUBITEM_DELIMITER, ' ').lower().strip())
    # split genre
    num = Book.get_filed_num('genres')
    row[num] = _make_list(row[num].lower().strip())
    row.append(archive_name)


def parse_inpx(filename: str, progress_cb: Callable[[int], None] = None) -> (Dict[str, Book], Dict[str, Book]):
    by_author = defaultdict(list)
    by_genre = defaultdict(list)
    book_fields_count = 14
    with ZipFile(filename, 'r') as inpx:
        files = [f for f in inpx.filelist if INP_PAT.match(f.filename)]
        for fnum, file in enumerate(files):
            # TODO: fix memory leaks. Use stream-parsing wrapper (find \n byte)
            inp_file_data = inpx.read(file.filename).decode('UTF-8').splitlines()
            for row in csv.reader(inp_file_data, delimiter=INPX_FIELD_DELIMITER):
                # ugly hack. We get 15 columns but we need only 14 (error in format of file)
                if len(row) < book_fields_count:
                    print(f'too low column count: {row}')
                    continue
                row = row[:book_fields_count]
                archive_filename = f'{os_path.splitext(file.filename)[0]}{os_path.extsep}{ARCHIVE_EXT}'
                _preprocess_row(row, os_path.join(os_path.dirname(filename), archive_filename))
                try:
                    book = Book(*row)
                except Exception as exc:
                    print(f'Error during convert row to book: {row}. {exc}')
                    continue
                for author in book.authors:
                    by_author[author].append(book)
                for genre in book.genres:
                    by_genre[genre].append(book)
            if progress_cb:
                progress_cb(int(fnum * 100 / len(files)))
            break
    return by_author, by_genre


def _create_book_dst_dir(book: Book, first_author_only: bool = False):
    if first_author_only:
        return BAD_DIR_CHARACTERS_PAT.sub(REPLACE_DIR_CHARACTER, book.authors[0].title())
    return BAD_DIR_CHARACTERS_PAT.sub(REPLACE_DIR_CHARACTER, ' '.join(book.camelcase_authors))


def _create_book_filename(book: Book, first_author_only: bool = False):
    if first_author_only:
        return BAD_DIR_CHARACTERS_PAT.sub(REPLACE_DIR_CHARACTER, f'{book.dst_short_filename} - {os.path.extsep}{book.ext}')
    return BAD_DIR_CHARACTERS_PAT.sub(REPLACE_DIR_CHARACTER, f'{book.dst_full_filename}{os.path.extsep}{book.ext}')


def extract_books(book_ids: Iterable[str], destination: str) -> List[str]:  # return an error
    errors = []
    for iid in book_ids:
        book = LIBRARY.books.get(iid)
        if book is None:
            print(f"Error: Can't find {iid}")
            continue
        book_dst_dir = os.path.join(destination, _create_book_dst_dir(book))
        if not os.path.exists(book_dst_dir):
            try:
                os.mkdir(book_dst_dir)
            except OSError as exc:
                if exc.errno == 36:
                    book_dst_dir = os.path.join(destination, _create_book_dst_dir(book, True))
                    try:
                        os.mkdir(book_dst_dir)
                    except Exception as exc:
                        errors.append(f"Can't create directory for book ({book.title}): '{book_dst_dir}'. {exc}")
                        continue
                raise
            except Exception as exc:
                errors.append(f"Can't create directory for book ({book.title}): '{book_dst_dir}'. {exc}")
                continue
        book_filename = f'{book.filename}.{book.ext}'
        book_full_path = os.path.join(book_dst_dir, book_filename)
        book_dst_full_name = _create_book_filename(book, False)
        book_dst_short_name = _create_book_filename(book, True)
        book_dst_full_path = os.path.join(book_dst_dir, book_dst_full_name)
        book_dst_short_path = os.path.join(book_dst_dir, book_dst_short_name)
        if os.path.exists(book_full_path):
            errors.append(f'Book already exists, skip: "{book_full_path}"')
            continue
        if os.path.exists(book_dst_full_path):
            errors.append(f'Book already exists, skip: "{book_dst_full_path}"')
            continue
        with ZipFile(book.archive_filename) as barch:
            barch.extract(book_filename, book_dst_dir)
            try:
                os.rename(book_full_path, book_dst_full_path)
            except OSError as exc:
                if exc.errno == 36:
                    try:
                        os.rename(book_full_path, book_dst_short_path)
                        errors.append(f'Book destination name too long. Use short name: "{book_dst_short_path}"')
                    except Exception as exc:
                        errors.append(f'Не могу переименовать "{book_full_path}" в {book_dst_short_path}')
                        continue
            except Exception as exc:
                errors.append(f'Произошла ошибка при распаковке "{book_full_path}", {book.view_title}')

    return errors



if __name__ == '__main__':
    ba, bg = parse_inpx("/media/hoske/My Passport/Library/fb2.Flibusta.Net/flibusta_fb2_local.inpx")
    # print(*[f'{k}:{len(v)}' for k, v in ba.items()], sep='\n')