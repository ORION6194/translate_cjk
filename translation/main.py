# coding=utf-8
import csv
import multiprocessing
import threading
import time
from concurrent.futures.thread import ThreadPoolExecutor

from translation import translate_inputs, config, logger
from langdetect import detect


print("Start")


class PreTranslationProcessing:
    def __init__(self):
        pass

    def get_all_elements_to_tuple(self, dict_row):
        """
        Gathers all elements of the row into a tuple to translate
        :param dict_row: row from .csv file
        :return: tuple of the elements of the row
        """
        result_tuple = ()
        for element in dict_row:
            if element is None or element.strip() == "":
                continue
            logger.debug("[Inside get_all_elements_to_tuple() in Main.py] element: " + str(element))
            result_tuple = result_tuple + (dict_row.get(element),)
        return result_tuple

    def get_translation_flag(self, country):
        """
        Get the translation flag for a language/country, ex. "en" for English-speaking countries
        :param country: country for which to get the translation flag; United States, England, China, Taiwan, or South Korea
        :return: Translation flag
        """
        country = country.strip().lower()
        if country == "united states" or country == "usa" or country == "us" or country == "britain" or country == "england":
            return "en"
        elif "china" in country:
            return "zh-CN"
        elif "taiwan" in country:
            return "zh-TW"
        elif "korea" in country:
            return "ko"
        elif "japan" in country:
            return "ja"
        return "zh"

    def detect_language(self, row):
        """
        Detect which language the row is in
        :param row: The row with the words to be translated
        """

        list_languages = ["ko", "zh", "zh-cn", "en", "ja"]
        languages_detected = {}
        for slot in list(row.values()):
            try:
                lang = detect(slot)  # detect language
                if languages_detected.get(lang) is None:
                    languages_detected[lang] = 1
                else:
                    languages_detected[lang] = languages_detected.get(lang) + 1
            except Exception as e:
                logger.debug("[Inside detect_language() in PreTranslationProcessing in main] Exception thrown: %s" % e)
        most_common_lang = "en"
        num_times_common_lang = 0
        for key in languages_detected:
            if languages_detected[key] > num_times_common_lang:
                most_common_lang = key
        if most_common_lang not in list_languages:
            most_common_lang = "en"
        try:
            if most_common_lang == detect(row):
                return most_common_lang
            else:
                return "en"
        except Exception as e:
            logger.debug("[Inside detect_language() in PreTranslationProcessing in main] Exception thrown: %s" % e)
        return most_common_lang


class PostTranslationProcessing:
    def __init__(self):
        pass

    def convert_tuple_to_dict(self, translated_row):
        """
        Converts the translated row that is now in tuple form into a dictionary which will be returned as the
        translated copy of the row
        :param translated_row: tuple of translation
        :return: translated dictionary to be written into the file
        """
        result_translated_row = {}
        for key in translated_row:
            if key is None or key.strip() == "":
                continue
            element = translated_row.get(key)
            if element is None:
                element = ("", "No translation")
            result_translated_row[str(key) + " Translated"] = element[0]
            result_translated_row[str(key) + " Translation Accuracy"] = element[1]
        return result_translated_row

    def insert_original(self, translated_row, row):
        """
        Insert the original value/words into the translated row for writing to file
        :param translated_row: dictionary with translation and accuracy
        :param row: original row from which to extract elements and combine them with translation and accuracy
        :return: expanded dictionary which consists of the union of translated_row and row
        """
        for key in row:
            if key is None or key.strip() == "":
                continue
            translated_row[key] = row.get(key)
        return translated_row


def translate_one_row(row, columns_to_translate):
    """
    Process one single row and returns a translated copy. The original row object is not changed.
    :param row: row to translate
    :return: copy of row that is translated.
    """
    if row is None or row == "":
        return None
    country_key = ""
    for key in row:
        if "country" in key:
            country_key = key
            break

    from_lang_code = PreTranslationProcessing().detect_language(row)
    to_lang_code = PreTranslationProcessing().get_translation_flag(row.get(country_key))

    translated_dict = translate_inputs.translate_all(row, columns_to_translate, from_lang=from_lang_code,
                                                     to_lang=to_lang_code)
    translated_row = PostTranslationProcessing().convert_tuple_to_dict(translated_dict)
    translated_row = PostTranslationProcessing().insert_original(translated_row, row)
    return translated_row


def row_thread(row, columns_to_translate, _lock, writer_good_results=None, good_result_file=None):
    """
    The method which the executor executes in one thread. Calls deal_each_row(row), writes the result to the files,
    and deals with exceptions by writing the row to the
    bad_result_file
    :param columns_to_translate: Which columns from the csv_file should be translated
    :param row: The row of the .csv file which is to be translated
    :param _lock: Universal Semaphore which is used to synchronously write to files
    :param writer_good_results: A csv.DictWriter object of good_result_file in which to write the translations
    :param good_result_file: The file in which the successful translations are to be written
    """
    try:
        logger.debug("[Inside row_thread(%s, %s, %s, %s, %s) in main] Begin row" %
                      (row, columns_to_translate, _lock, writer_good_results, good_result_file))
        result = translate_one_row(row, columns_to_translate)
        if result is -1 or 0:  # we do not deal with this country yet
            return
        with _lock:
            writer_good_results.writerow(result)
            good_result_file.flush()  # file is updated immediately
            logger.debug("[Inside row_thread() in main] Writing to valid file")

    except Exception as e:
        logger.exception("[Inside row_thread() in main] Exception thrown")
        row["other"] = "Exception was thrown" + str(e)
        with _lock:
            updated_row = {}
            for key in row:
                if key is None or key.strip() == "":
                    continue
                updated_row[str(key)] = row.get(key)
                updated_row[str(key) + " Translated"] = ""
                updated_row[str(key) + " Translation Accuracy"] = "Failed - Exception was thrown; " + str(e)
            writer_good_results.writerow(updated_row)
            good_result_file.flush()  # file is updated immediately
            logger.debug("[Inside row_thread() in main] Writing to flagged file")


def expand_fieldnames(fieldnames, columns_to_translate):
    """
    Expand the list of fieldnames for the final result document to include not only the original version,
    but also the translation and the translation accuracy
    :param fieldnames: (list) original fieldnames
    :param columns_to_translate: (list) the names of the columns to translate
    :return:
    """
    expanded_fieldnames = []
    for col in columns_to_translate:
        if col not in fieldnames:
            raise Exception("Column Name: " + str(col) + " does not exist")
    for name in fieldnames:
        if name is None or name.strip() == "":
            continue
        if name in columns_to_translate:
            expanded_fieldnames.append("")
            expanded_fieldnames.append(name)
            expanded_fieldnames.append(name + " Translated")
            expanded_fieldnames.append(name + " Translation Accuracy")
            expanded_fieldnames.append("")
        else:
            expanded_fieldnames.append(name)
    return expanded_fieldnames


def skip_row(row):
    """
    See if the row should be skipped. i.e. there is no content in that row, then don't bother running that row
    through the translations.
    :param row: the tuple/row in the file to translate
    :return: True is row should be skipped (i.e. no content to translate in row) or False if row needs to be translated
    """
    if row is None or str(row).strip() == "":
        return True
    for value in row.values():
        if value.strip() != "":
            return False
    return True


def start_translate_file(read_file, good_file, columns_to_translate=None):
    """
    Main Beginning of program when translating an entire .csv file.
    Reads from file_read and writes out results to either good_file or bad_file.
    Submits each row to an Executor which then executes row_thread() to get a translation
    :param columns_to_translate: Names of the columns on the document to translate
    :param read_file: File from which to read the data
    :param good_file: File to write data during which an uncaught exception had been thrown
    """

    # Config logging file
    # logging.basicConfig(handlers=[logging.FileHandler(config.LOGGING_FILE, "w", config.LOGGING_ENCODING)],
    #                     level=config.LOGGING_LEVEL, format=config.LOGGING_FORMAT, datefmt=config.LOGGING_DATE_FORMAT)
    with open(read_file, encoding=config.KAFKA_ENCODING, newline='\n') as english_file:
        with open(good_file, "w", encoding="utf8", newline='\n') as good_result_file:
            reader = csv.DictReader(english_file)

            if columns_to_translate is None or len(columns_to_translate) == 0:
                columns_to_translate = reader.fieldnames
            fieldnames = expand_fieldnames(reader.fieldnames, columns_to_translate)
            fieldnames.append("other")
            writer_good_results = csv.DictWriter(good_result_file, fieldnames=fieldnames)
            writer_good_results.writeheader()
            try:
                _lock = threading.Lock()
                threads = []
                number_processors = multiprocessing.cpu_count()
                with ThreadPoolExecutor(max_workers=number_processors) as pool_rows:
                    for row in reader:
                        if skip_row(row):
                            continue
                        logger.debug("[Inside start() in main] Row: " + str(row))
                        threads.append(pool_rows.submit(row_thread, row, columns_to_translate, _lock,
                                                        writer_good_results, good_result_file))
                    for thread in threads:
                        logger.debug("[Inside row_thread(%s, %s, %s, %s, %s, %s, %s) in main] result from thread: "
                                      + str(thread.result(timeout=180)))
                        threads.remove(thread)
                logger.debug("[Inside start() in main] After")
            except Exception as e:
                print(e)
                logger.debug("[Inside start() in main] Exception thrown: " + str(e))


def test_program():
    """
    Run some documents through to test the translation service
    """
    curr_time = time.time()
    file_to_translate = config.FILE_TO_TRANSLATE
    file_good = config.FILE_TRANSLATED_RESULT
    columns_to_translate = config.COLUMNS_TO_TRANSLATE
    start_translate_file(read_file=file_to_translate, good_file=file_good, columns_to_translate=columns_to_translate)
    print("Amount of time to run the program: " + str(time.time() - curr_time) + " seconds")
    print("End")


if __name__ == "__main__":
    test_program()
