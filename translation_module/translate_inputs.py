import multiprocessing
from ast import literal_eval
from concurrent.futures.thread import ThreadPoolExecutor

import requests
import translation as trans
from fuzzywuzzy import process
from googletrans import Translator as googletrans_Translator
from translate import Translator as translate_Translator
from translation_module import logger, config


class TranslationResources:
    def __init__(self):
        pass

    def translator_translate(self, input_str, to_lang):
        """
        Translate input using Python module translation
        :param input_str: The string to translate
        :param to_lang:  Language flag, ex. "zh", to which to translate input_str
        :return: Translation that is produced
        """
        translator = translate_Translator(to_lang=to_lang)
        translation1 = translator.translate(input_str)
        return translation1

    def yandex_translation(self, input_str, from_lang, to_lang):
        """
        Translation of input_str using Yandex translation
        :param input_str: The string to translate
        :param from_lang: Language flag, ex. "en", from which to translate input_str
        :param to_lang: Language flag, ex. "zh", to which to translate input_str
        :return: Translation if Yandex produces a response, or else None
        """
        first_part = "https://translate.yandex.net/api/v1.5/tr.json/translate?"
        key = "key=" + config.get_yandex_api_key()
        text = "&text=" + input_str
        lang = "&lang=" + from_lang.strip() + "-" + to_lang.strip()
        website = first_part + key + text + lang
        # print(website)
        response = requests.get(website, headers={'User-Agent': 'Mozilla/5.0'})
        response = literal_eval(response.text).get("text")
        if response is None:
            return None
        elif len(response) == 1:
            return response[0]
        else:
            return response

    def google_translation(self, input_str, from_lang, to_lang):
        """
        Use two resources to translate input_str using Google Translation from from_lang to to_lang
        :param input_str: The string to translate
        :param from_lang: Language flag, ex. "en", from which to translate input_str
        :param to_lang: Language flag, ex. "zh", to which to translate input_str
        :return: Translation from one of the sources if only one produces a translation.
                 None if neither produce a translation or if the two resources produce different translations
        """
        logger.debug("Entered google_translation(%s, %s, %s) in translate_inputs.py" % (input_str, from_lang, to_lang))
        translator = googletrans_Translator(service_urls=['translate.google.cn', "translate.google.com"])
        response1 = translator.translate(input_str, src=from_lang, dest=to_lang).text
        response2 = None
        try:
            response2 = trans.google(input_str, src=from_lang, dst=to_lang)
            logger.debug("[Inside google_translation() in translate_inputs.py] Response from translator.translate: %s;"
                          " Response from trans.google: %s" % (response1, response2))
        except Exception as e:
            logger.debug("[Inside google_translation() in translate_inputs.py] Exception thrown: %s" % e)
        if response1 is None and response2 is not None:
            return response2
        elif response1 is not None and response2 is None:
            return response1
        elif response1 == response2:
            return response1
        return None

    def switch_flag(self, to_lang, from_lang, switch_to):
        korean_flags = ["ko", "kor", "kr"]
        if from_lang in korean_flags and switch_to in korean_flags:
            from_lang = switch_to
        if to_lang in korean_flags and switch_to in korean_flags:
            to_lang = switch_to

        mandarin_flags = ["zh", "zh-CN", "zh-CHS", "zh-TW"]
        if from_lang in mandarin_flags and switch_to in mandarin_flags:
            from_lang = switch_to
        if to_lang in mandarin_flags and switch_to in mandarin_flags:
            to_lang = switch_to

        japanese_flags = ["ja", "jp"]
        if from_lang in japanese_flags and switch_to in japanese_flags:
            from_lang = switch_to
        if to_lang in japanese_flags and switch_to in japanese_flags:
            to_lang = switch_to

        return to_lang, from_lang

    def get_translations(self, input_str, from_lang, to_lang):
        """
        Use multiple resources to translate the input_str.
        Python packages used: translate, translation, google trans, and also the yandex api
        :param input_str: String: Input string to be translated from from_lang to to_lang
        :param from_lang: Language flag, ex. "zh", from which language to translate input_str
        :param to_lang: Language flag, ex. "en", to which language to translate input_str
        :return: List all the translations
        """
        if input_str is None or input_str.strip() == "" or not bool(from_lang) or not bool(to_lang):
            return ""
        python_module_translation, yandex, google, baidu, bing, youdao, iciba = None, None, None, None, None, None, None
        with ThreadPoolExecutor(max_workers=7) as executor:
            to_lang, from_lang = self.switch_flag(to_lang=to_lang, from_lang=from_lang, switch_to="zh-CN")
            to_lang, from_lang = self.switch_flag(to_lang=to_lang, from_lang=from_lang, switch_to="zh-TW")
            to_lang, from_lang = self.switch_flag(to_lang=to_lang, from_lang=from_lang, switch_to="ko")
            to_lang, from_lang = self.switch_flag(to_lang=to_lang, from_lang=from_lang, switch_to="ja")
            python_module_executor = executor.submit(self.translator_translate, input_str, to_lang)

            yandex_executor = executor.submit(self.yandex_translation, input_str, from_lang, to_lang)

            google_executor = executor.submit(self.google_translation, input_str, from_lang, to_lang)

            to_lang, from_lang = self.switch_flag(to_lang=to_lang, from_lang=from_lang, switch_to="kr")
            youdao_executor = executor.submit(trans.youdao, input_str, from_lang, to_lang)

            to_lang, from_lang = self.switch_flag(to_lang=to_lang, from_lang=from_lang, switch_to="zh")
            to_lang, from_lang = self.switch_flag(to_lang=to_lang, from_lang=from_lang, switch_to="zh-TW")
            to_lang, from_lang = self.switch_flag(to_lang=to_lang, from_lang=from_lang, switch_to="kor")
            to_lang, from_lang = self.switch_flag(to_lang=to_lang, from_lang=from_lang, switch_to="jp")
            baidu_executor = executor.submit(trans.baidu, input_str, from_lang, to_lang)

            to_lang, from_lang = self.switch_flag(to_lang=to_lang, from_lang=from_lang, switch_to="ko")
            iciba_executor = executor.submit(trans.iciba, input_str, from_lang, to_lang)

            to_lang, from_lang = self.switch_flag(to_lang=to_lang, from_lang=from_lang, switch_to="zh-CHS")
            to_lang, from_lang = self.switch_flag(to_lang=to_lang, from_lang=from_lang, switch_to="zh-TW")
            bing_executor = executor.submit(trans.bing, input_str, from_lang, to_lang)

            try:
                python_module_translation = python_module_executor.result(timeout=6)
            except Exception as e:
                logger.debug("[Inside get_translations() in translate_inputs.py] python_module_translation: %s" % e)
            try:
                yandex = yandex_executor.result(timeout=6)
            except Exception as e:
                logger.debug("[Inside get_translations() in translate_inputs.py] yandex: %s" % e)
            try:
                google = google_executor.result(timeout=6)
            except Exception as e:
                logger.debug("[Inside get_translations() in translate_inputs.py] google: %s" % e)

            try:
                baidu = baidu_executor.result(timeout=6)
            except Exception as e:
                logger.debug("[Inside get_translations() in translate_inputs.py] baidu: %s" % e)
            try:
                bing = bing_executor.result(timeout=6)
            except Exception as e:
                logger.debug("[Inside get_translations() in translate_inputs.py] bing: %s" % e)
            try:
                youdao = youdao_executor.result(timeout=6)
                if youdao == "您的请求来源非法，商业用途使用请关注有道翻译API官方网站“有道智云”: http://ai.youdao.com":
                    youdao = None
            except Exception as e:
                logger.debug("[Inside get_translations() in translate_inputs.py] youdao: %s" % e)
            try:
                iciba = iciba_executor.result(timeout=6)
            except Exception as e:
                logger.debug("[Inside get_translations() in translate_inputs.py] iciba: %s" % e)
        logger.debug("[Inside get_translations() in translate_inputs.py] Result: [%s, %s, %s, %s, %s, %s, %s]"
                      % (python_module_translation, yandex, google, baidu, bing, youdao, iciba))
        return [python_module_translation, yandex, google, baidu, bing, youdao, iciba]


def get_translations_wrapper(input_str, from_lang, to_lang):
    """
    Wrapper around the get_translations method which also compares the results using compare_translations()
    :param input_str: String: Input string to be translated from from_lang to to_lang
    :param from_lang: Language flag, ex. "zh", from which language to translate input_str
    :param to_lang: Language flag, ex. "en", to which language to translate input_str
    :return: Most common translation of input_str if successful, or else return input_str
    """
    translations = TranslationResources().get_translations(input_str, from_lang, to_lang)
    final = compare_translations(tuple(translations), to_lang)
    if final is None or final == "":
        return ""
    else:
        return final


def deal_translation(element, from_lang, to_lang):
    """
    Translates the element from from_lang to to_lang. Translates that result back to from_lang and compares that result
    with the original element.
    :param element: string to be translated
    :param from_lang: language the element is currently in
    :param to_lang: language to translate the element to
    :return: tuple containing the translation and the accuracy of the translation
    """
    translation = get_translations_wrapper(element, from_lang=from_lang, to_lang=to_lang)
    translated_back_list = TranslationResources().get_translations(translation, from_lang=to_lang, to_lang=from_lang)
    if translated_back_list is None or str(translated_back_list).strip() == "":
        return translation, "Failed to translate"
    result = process.extractOne(element, translated_back_list)
    logger.info("Original: %s;\t Translation: %s;\t Accuracy: %s" % (element, translation, result[1]))
    print("Original: %s;\t Translation: %s;\t Accuracy: %s" % (element, translation, result[1]))
    return translation, result[1]


def translate_all(dict_input, columns_to_translate, from_lang="en", to_lang="zh"):
    """
    Translates the input_strs from the from_lang to the to_lang using multiple resources and then checks that by
    translating back and comparing the result to the original.
    :param input_strs: tuple of strings inputted to translate
    :param from_lang: language flag to translate from
    :param to_lang: language flag to translate to
    :return: Tuple of the translations
    """
    index = 0
    threads = {}
    translated_dict_input = {}
    logger.debug("[Inside translate_all() in translate_inputs.py] len(dict_input): %s" % len(dict_input))
    with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        for key in dict_input:
            if key not in columns_to_translate:
                continue
            try:
                element = dict_input.get(key)
                if element is None or str(element).strip() == "":
                    threads[key] = None
                else:
                    threads[key] = executor.submit(deal_translation, element, from_lang, to_lang)
                index += 1
            except Exception as e:
                logger.debug("[Inside translate_all() in translate_inputs.py] executor.submit() Exception: %s" % e)
        for key in threads:
            if threads.get(key) is None:
                translated_dict_input[key] = ("", "")
            else:
                try:
                    translated_dict_input[key] = threads.get(key).result(timeout=60)
                except Exception as e:
                    logger.debug("[Inside translate_all() in translate_inputs.py] thread.result() Exception: %s" % e)
                    translated_dict_input[key] = ("", "Failed; " + str(e))
    return translated_dict_input


class CharacterUnicodeCheck:
    """
    Check the character's code to identify if the word(s) were translated
    """

    def __init__(self, translate_to_language):
        self.translate_to_language = translate_to_language

    def has_cjk_letters(self, translated_words):
        """
        checks if input contains any non-English letters, which means that a translation occurred from English to a
        foreign language
        :param translated_words: string of words
        :return: True: There are non-English letters
                 False: There are English letters
        """
        i = 0
        list_range = [(0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0x3000, 0x303F), (0x20000, 0x2A6DF), (0x2A700, 0x2B73F),
                      (0x2B740, 0x2B81F), (0x2B820, 0x2CEAF), (0xF900, 0xFAFF), (0x2F800, 0x2FA1F)]
        if "ko" in self.translate_to_language or "kr" in self.translate_to_language:
            list_range.append((0xAC00, 0xD7AF))
            list_range.append((0x1100, 0x11FF))

        while i < len(translated_words):
            # check the unicode of the letters to see if one is within the range between 0x4E00 and 0x9FAF,
            for range_tuple in list_range:
                if range_tuple[0] < ord(translated_words[i]) < range_tuple[1]:
                    return True
            i += 1
        return False

    def all_other_letters(self, translated_words):
        """
        checks if input contains any English letters, which means that a translation occurred from a foreign language
        to English
        :param translated_words: string of words
        :return: True: There are non-English letters
                 False: There are English letters
        """
        i = 0
        while i < len(translated_words):
            # check the unicode of the letters to see if they are between the range of 64 and 128,
            if 0x0041 <= ord(translated_words[i]) <= 0x007A:
                return True
            i += 1
        return False

    def has_english_letters(self, translated_words):
        """
            checks if input contains any English letters, which means that a translation occurred from a foreign language
            to English
            :param translated_words: string of words
            :return: True: There are non-English letters
                     False: There are English letters
            """
        if "en" not in self.translate_to_language:
            raise Exception("en not in self.translate_to_language")
        i = 0
        while i < len(translated_words):
            # check the unicode of the letters to see if they are between the range of 64 and 128,
            if 0x0041 <= ord(translated_words[i]) <= 0x007A:
                return True
            i += 1
        return False


def was_translated(translate_to_language):
    """
    Get the function
    :param translate_to_language: language flag for language that the translation should be translated into.
    :return: function for which the translation should be checked to ensure that a translation occurred (by checking if
    at least one of the characters is part of the translate_to_language language)
    """
    if "en" in translate_to_language:
        return CharacterUnicodeCheck(translate_to_language).has_english_letters
    elif "zh" in translate_to_language or "ko" in translate_to_language or "ja" in translate_to_language:
        return CharacterUnicodeCheck(translate_to_language).has_cjk_letters
    return CharacterUnicodeCheck(translate_to_language).all_other_letters


def compare_translations(translations, translate_to_language="zh"):
    """
    Compares the translations from multiple sources and counts the number of same translations and returns the
    translation from the most sources. In cases of tie, goes with earlier source.
    :param translate_to_language: language translations should be in: removes any translations which were not translated
    :param translations: tuple of translations
    :return: translation as translated by most sources
    """
    # first, write all the translations to a dictionary with the key being the translation and the value being the
    # number of times the translation appears in the sources
    dict_translations = {}
    yes_translated = was_translated(translate_to_language)
    for translation1 in translations:
        try:
            if translation1 is None or not yes_translated(translation1):
                continue
        except Exception as e:
            logger.debug("[Inside compare_translations() in translate_inputs.py] yes_translated(%s) Exception: %s" %
                          (translation1, e))
        if dict_translations.get(translation1) is None:
            dict_translations[translation1] = 1
        else:
            dict_translations[translation1] = dict_translations.get(translation1) + 1

    # second, compare the values and find which translation appears the most times
    biggest_num = 0
    biggest_translation = None
    for translation1 in dict_translations:
        num_times = dict_translations.get(translation1)
        if num_times > biggest_num:
            biggest_num = num_times
            biggest_translation = translation1
    return biggest_translation

# print("result: " + str(trans.bing("Hello How are you", src="en", dst="ko", proxies={'http': '192.168.89.3:8080'})))
# print("Get language: " + detect("您的请求来源非法，商业用途使用请关注有道翻译API官方网站“有道智云"))
# print(TRANSLATION_DICT["bing"]("Hello How are you", "en", "ko", proxies={'http': '127.0.0.1:1080'}))
# print("Finished")
