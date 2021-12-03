import unicodedata
from typing import Optional, List, Dict, Union

import bs4
import re

from scrc.enums.language import Language
from scrc.enums.section import Section
from scrc.utils.main_utils import clean_text
from scrc.enums.court_role import CourtRole
from scrc.enums.gender import Gender

"""
This file is used to extract sections from decisions sorted by spiders.
The name of the functions should be equal to the spider! Otherwise, they won't be invocated!
Overview of spiders still todo: https://docs.google.com/spreadsheets/d/1FZmeUEW8in4iDxiIgixY4g0_Bbg342w-twqtiIu8eZo/edit#gid=0
"""

x = 0


def XX_SPIDER(decision: Union[bs4.BeautifulSoup, str], namespace: dict) -> Optional[Dict[Section, List[str]]]:
    """
    :param decision:    the decision parsed by bs4 or the string extracted of the pdf
    :param namespace:   the namespace containing some metadata of the court decision
    :return:            the sections dict (keys: section, values: list of paragraphs)
    """
    # This is an example spider. Just copy this method and adjust the method name and the code to add your new spider.
    pass


def VD_FindInfo(decision: Union[bs4.BeautifulSoup, str], namespace: dict) -> Optional[Dict[Section, List[str]]]:
    def get_paragraphs(soup):
        """
        Get composition of the decision
        :param soup:
        :return:
        """
        paragraphs = []
        # by some bruteforce I have found out that the html files in
        # VD_FindInfo either do not have class type or they have three divs with class type Section{1,2,3}
        # Therefore, we need to check for two cases
        divs = []
        # First case
        divs = soup.find_all("div", class_=False)
        # Second case
        if len(divs) == 0:
            for s in ["Section1", "Section2", "Section3"]:
                divs_temp = soup.find_all("div", class_=s)
                if len(divs_temp) == 1:
                    divs.append(divs_temp[0])
                else:
                    continue
        # If no div is returned raise an error
        if len(divs) == 0:
            f = open("VD_FindInfo_missed_htmls.txt", "a")
            f.write('%s' % soup)
            f.write('\n-------------------------------------------------------------\n')
            f.close()
            message = f"Different html structure!"
            raise ValueError(message)
        # some of the keywords (composition, president) are inside <span> and element.string does not retrieve them
        # therefore, we have to use the text method

        for div in divs:
            if isinstance(div, bs4.element.Tag):
                paragraph = clean_text(div.text)
                if paragraph not in ['', ' ', None]:  # discard empty paragraphs
                    paragraphs.append(paragraph)
        return paragraphs

    def get_composition_candidates(paragraphs, cm_RegEx, cm_end_RegEx):

        composition_candidate = None

        for paragraph in paragraphs:

            cm_start_ = cm_RegEx.search(paragraph)
            if cm_start_ is None:
                continue
            else:
                # cm_end.start() would be relative to cm_start_.start()
                cm_end = cm_end_RegEx.search(paragraph[cm_start_.end():])

                if cm_end is None:
                    continue
                else:
                    # # we need to handle one stupid corner case
                    # stupid_corner_case_RegEx = re.compile(r'juuuuujuujujujuges')
                    # if stupid_corner_case_RegEx.search(paragraph) is not None:
                    #     continue
                    composition_candidate = paragraph[cm_start_.start():cm_start_.end() + cm_end.start()]
                break

            # Store all the compositions in a signle list

        return composition_candidate

    #############################################SHOULD BE MOVED TO THE COURT COMPOSITION FILE
    def find_the_keywords(candidate):
        """

                @param candidate: a string which should contain the judicial people @return: a dictionary with roles
                as keys and each value contains a tuple of 1)Boolean value indicating whether the role is available
                or not 2) the span of occurrence of the role's keyword
        """
        cm_start_available, cm_end_available, vpr_available, pr_available, as_available, gr_available, ju_available, ju_as_available, ju_su_available, ju_dl_available, ti_available = False, False, False, False, False, False, False, False, False, False, False
        cm_start_span, cm_end_span, vpr_span, pr_span, as_span, gr_span, ju_span, ju_as_span, gr_span, ju_su_span, ju_dl_span, ti_span_list = None, None, None, None, None, None, None, None, None, None, None, None
        vpr_gender, pr_gender, as_gender, gr_gender, ju_gender, ju_as_gender, ju_su_gender, ju_rp_gender, ju_dl_gender = None, None, None, None, None, None, None, None, None

        cm_start_ = cm_start_RegEx.search(candidate)
        cm_end_ = cm_end_RegEx.search(candidate)
        pr_ = pr_RegEx.search(candidate)
        vpr_ = vpr_RegEx.search(candidate)
        as_ = as_RegEx.search(candidate)
        gr_ = gr_RegEx.search(candidate)
        ju_ = ju_RegEx.search(candidate)
        ju_as_ = ju_as_RegEx.search(candidate)
        ju_dl_ = ju_dl_RegEx.search(candidate)
        ju_su_ = juSup_RegEx.search(candidate)
        ti_ = ti_RegEx.search(candidate)

        # we can find the gender by the gender of the role used. In french they add an extra 'e' or 'se' for feminine
        feminine_roles_RegEx = re.compile(r'[P,p]r[é,e]sidente|[A,a]ssesseu(re|se)|[G,g]reffi[e,è]re|'
                                          r'suppl[é,e]ant(e)|rapporteu(re|se)|La\b')
        masculine_roles_RegEx = re.compile(r'[P,p]r[é,e]sident(s)?\b|[A,a]ssesseur(s)?\b|[G,g]reffi[e,è]r(s)?\b|'
                                           r'suppl[é,e]ant\b|rapporteur\b|Le\b')

        if cm_start_ is not None:
            cm_start_available = True
            cm_start_span = cm_start_.span()

        if cm_end_ is not None:
            cm_end_available = True
            cm_end_span = cm_end_.span()

        if pr_ is not None:
            pr_available = True
            pr_span = pr_.span()
            if feminine_roles_RegEx.search(candidate[pr_span[0]:pr_span[1]]):
                pr_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[pr_span[0]:pr_span[1]]):
                pr_gender = Gender.MALE
            else:
                pr_gender = None

        if vpr_ is not None:
            vpr_available = True
            vpr_span = vpr_.span()
            if feminine_roles_RegEx.search(candidate[vpr_span[0]:vpr_span[1]]):
                vpr_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[vpr_span[0]:vpr_span[1]]):
                vpr_gender = Gender.MALE
            else:
                vpr_gender = None

        if as_ is not None:
            as_available = True
            as_span = as_.span()
            if feminine_roles_RegEx.search(candidate[as_span[0]:as_span[1]]):
                as_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[as_span[0]:as_span[1]]):
                as_gender = Gender.MALE
            else:
                as_gender = None

        if gr_ is not None:
            gr_available = True
            gr_span = gr_.span()
            if feminine_roles_RegEx.search(candidate[gr_span[0]:gr_span[1]]):
                gr_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[gr_span[0]:gr_span[1]]):
                gr_gender = Gender.MALE
            else:
                gr_gender = None

        if ju_ is not None:
            ju_available = True
            ju_span = ju_.span()
            if feminine_roles_RegEx.search(candidate[ju_span[0]:ju_span[1]]):
                ju_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[ju_span[0]:ju_span[1]]):
                ju_gender = Gender.MALE
            else:
                ju_gender = None

        if ju_as_ is not None:
            ju_as_available = True
            ju_as_span = ju_as_.span()
            if feminine_roles_RegEx.search(candidate[ju_as_span[0]:ju_as_span[1]]):
                ju_as_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[ju_as_span[0]:ju_as_span[1]]):
                ju_as_gender = Gender.MALE
            else:
                ju_as_gender = None

        if ju_dl_ is not None:
            ju_dl_available = True
            ju_dl_span = ju_dl_.span()
            if feminine_roles_RegEx.search(candidate[ju_dl_span[0]:ju_dl_span[1]]):
                ju_dl_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[ju_span[0]:ju_span[1]]):
                ju_dl_gender = Gender.MALE
            else:
                ju_dl_gender = None

        if ju_su_ is not None:
            ju_su_available = True
            ju_su_span = ju_su_.span()
            if feminine_roles_RegEx.search(candidate[ju_su_span[0]:ju_su_span[1]]):
                ju_su_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[ju_su_span[0]:ju_su_span[1]]):
                ju_su_gender = Gender.MALE
            else:
                ju_su_gender = None

        if ti_ is not None:
            ti_available = True
            ti_span_list = [m.span() for m in re.finditer(ti_RegEx, candidate)]

        # to handle the corner case when we have ju_su or ju_as or ju_rp but not the ju
        if ju_available and ju_as_available:
            if ju_span[0] == ju_as_span[0]:
                ju_available = False
        if ju_available and ju_su_available:
            if ju_span[0] == ju_su_span[0]:
                ju_available = False
        if ju_available and ju_dl_available:
            if ju_span[0] == ju_dl_span[0]:
                ju_available = False
        if ju_as_available and as_available:
            if ju_as_span[0] < as_span[0] and ju_as_span[1] >= as_span[1]:
                as_available = False
        keyword_dict = {
            'cm_start': [cm_start_available, cm_start_span],
            'cm_end': [cm_start_available, cm_end_span],
            'pr': [pr_available, pr_span, pr_gender],
            'vpr': [vpr_available, vpr_span, vpr_gender],
            'as': [as_available, as_span, as_gender],
            'gr': [gr_available, gr_span, gr_gender],
            'ju': [ju_available, ju_span, ju_gender],
            'ju_as': [ju_as_available, ju_as_span, ju_as_gender],
            'ju_dl': [ju_dl_available, ju_dl_span, ju_dl_span],
            'ju_su': [ju_su_available, ju_su_span, ju_su_gender],
            'ti': [ti_available, ti_span_list]
        }
        return keyword_dict

    def eliminate_invalid_roles(keyword_dict):
        """

        @param keyword_dict: receives a dictionary with keys = role and values = tuples of bool (availability of the role)
        and the span of the keyword
        @return: returns a dictionary of roles whose availability field is True
        """
        invalid_roles = []
        for k, v in keyword_dict.items():
            # if a role is not found, mark it as invalid
            if not v[0]:
                invalid_roles.append(k)
        for k in invalid_roles:
            keyword_dict.pop(k)
        return keyword_dict

    def extraction_using_titles(ti_, candidate, keywords):
        """

        @param ti_: a list of title's span()
        @param candidate: a string which is candidate for containing the composition
        @param keywords: a list of sorted roles and their span()
        @return:
        """
        roles = []

        idx_val = 0
        idx_title = 0
        prev_role = None
        next_role = None

        for val in keywords:

            if (idx_title == len(ti_)):
                print(candidate)
                print(roles)
                print(val)
                print(keywords)
                message = f"Extraction using title is not possible"
                raise ValueError(message)
            ti_e = ti_[idx_title]

            if idx_val < len(keywords) - 1:
                next_role = keywords[idx_val + 1][1][1]

            if prev_role is not None:

                # Several people have the same role
                # This naturally holds if names appear after the role
                while ti_e[0] < prev_role[0] and idx_title < len(ti_) - 1:
                    # I should go to next title
                    idx_title += 1
                    ti_e = ti_[idx_title]

            # the person's name and title are mentioned before their roles
            if ti_e[0] < val[1][1][0]:
                roles.append([val[0], candidate[ti_e[0]:val[1][1][0]], val[1][2]])  # ti_start to role start
            # the person's name and title are mentioned after their roles
            else:
                # Is it the last item?
                if idx_val == len(keywords) - 1:
                    roles.append([val[0], candidate[val[1][1][1]:], val[1][2]])
                # we are either at the beginning or at the middle
                else:
                    # we are in the middle
                    if next_role is not None:
                        roles.append(
                            [val[0], candidate[ti_e[0]:next_role[0]], val[1][2]])  # ti_start to next_role_start
                    else:  # we should not end up here
                        assert False
            prev_role = val[1][1]
            # increase the indexes for next loop
            idx_val += 1
            idx_title += 1

        return roles

    def extraction_using_composition(cm_, candidate, keywords):
        """
        @param cm_: The output of cm_RegEx. We can call its span() method to find where it occurs in the string
        @param candidate: a 400-character string which potentially contains the composition
        @param keywords: a sorted list of roles and their span
        @return: A list of tuples whith 1)the role keyword 2) their details
        """
        roles = []
        idx_val = 0
        prev_role = None
        next_role = None
        # for role in keywords
        for val in keywords:
            # If we are not at the end, store the next role in next_role variable
            if idx_val != len(keywords) - 1:
                next_role = keywords[idx_val + 1]
            # if composition_end is within president_start+5 then names come after their roles
            if cm_[1][1] + 5 > val[1][1][0]:
                # if we are not at the end
                if idx_val != len(keywords) - 1:
                    roles.append(
                        [val[0], candidate[val[1][1][1]:next_role[1][1][0]],
                         val[1][2]])  # current_role_end to next_role_start
                # the last person details
                else:
                    roles.append([val[0], candidate[val[1][1][1]:], val[1][2]])
            # otherwise, the names appear before the keyword
            else:
                # we have just started
                if idx_val == 0:
                    roles.append(
                        [val[0], candidate[cm_[1][1]:val[1][1][0]], val[1][2]])  # composition_end to role_begin
                # if we are in between
                elif idx_val != len(keywords) - 1:
                    roles.append(
                        [val[0], candidate[prev_role[1][1][1]:val[1][1][0]],
                         val[1][2]])  # prev_role_end to current_role_start
                else:
                    # some times we have 'Greffiere: name'
                    if candidate[val[1][1][1] + 1] == ':' or candidate[val[1][1][1] + 2] == ':':
                        roles.append([val[0], candidate[val[1][1][1]:val[1][1][1] + 25], val[1][2]])
                    else:
                        roles.append(
                            [val[0], candidate[prev_role[1][1][1]:val[1][1][0]],
                             val[1][2]])  # prev_role_end to current_role_start

            # we need to store the prev_role for cases when one role has several titles
            prev_role = val
            # increase the indexes for next loop
            idx_val += 1
        return roles

    def extract_judicial_people(candidate):
        """

        @param candidates: the string candidates for compostion
        @return: a list of tuples with judicial people's 1) role 2)their details
        """

        # iterate over all the candidates

        # find all the keyword's occurance in the candidate
        keywords = find_the_keywords(candidate)
        # pop out composition, and titles
        cm_start_ = keywords.pop('cm_start')
        cm_end_ = keywords.pop('cm_end')
        ti_ = keywords.pop('ti')
        # it is vital to see if titles are used or not
        ti_available = ti_[0]
        ti_ = ti_[1]
        # preprocessing: eliminate those roles that were not found
        keywords = eliminate_invalid_roles(keywords)
        # preprocessing: sort the roles based on their order (which comes earlier?)
        sorted_keywords = sorted(keywords.items(), key=lambda e: e[1][1][0])

        if ti_available is not False and len(ti_) >= len(keywords.items()):

            role = extraction_using_titles(ti_, candidate, sorted_keywords)

        # if titles are not used or not everybody has a title
        else:
            # we may be able to extract people using the composition keyword
            if cm_start_[0]:
                role = extraction_using_composition(cm_start_, candidate, sorted_keywords)
            else:
                message = f"We still do not support extraction without tiles and 'composition' keyword"
                raise ValueError(message)
        return role

    def remove_special_characters(in_str):
        """

        @param in_str: Input string
        @return: output string without the following characters: {",",";","s:","e:","******"}
        """
        # for ch in characters_to_replace:
        in_str = in_str.replace(",", "")
        in_str = in_str.replace(";", "")
        # some times roles are female or plural
        in_str = in_str.replace("s:", "")
        in_str = in_str.replace("e:", "")
        # remove sequences of '*'
        star_RegEx = re.compile(r'\*+')
        star_ = star_RegEx.search(in_str)
        if star_ is not None:
            star_s = star_.span()
            in_str = in_str[:star_s[0] - 1] + in_str[star_s[1] + 1:]
        return in_str

    def first_last_name(full_name, detail):
        """

        @param full_name: A string that potentially contains: first name (or initials) and last name
        @param detail: a dictionary which contains the details of the judicial people
        @return: the detail dictionary with two new records: first name (or initials) and last name
        """
        dot_RegEx = re.compile(r'\w\.\b')
        dot_ = dot_RegEx.search(full_name)
        names = full_name.split(" ")
        last_name = False
        # remove all the empty strings or strings of length 1
        for idx, name in enumerate(names):
            if name == "" or len(name) == 1:
                names.pop(idx)
        for name in names:
            # is it intials?
            if (dot_ is not None):
                detail['initials']: name
                last_name = True
            # is it the first or the last name?
            # In some decisions, we only have the last name
            elif (len(names) > 1 and last_name == False):
                detail['first name'] = name
                last_name = True
            else:
                detail['last name'] = name
        return

    def extract_details(roles):
        """

        @param roles: a list of tuples with judicial people's 1) role 2) details
        @return: A dictionary ready to be written in the json file
        """
        roles_keys = {'pr': CourtRole.PRESIDENT, 'vpr': CourtRole.VICE_PRESIDENT, 'as': CourtRole.ASSESSOR,
                      'gr': CourtRole.CLERK, 'ju': CourtRole.JUDGE, 'ju_su': CourtRole.JUDGE_SUPPLEMENTARY,
                      'ju_rp': CourtRole.JUDGE_REPORTER, 'ju_dl': CourtRole.DELEGATE_JUDGE}
        feminine_titles = ['Mme', 'Mme.', 'Mmes', 'Mlle', 'Mlle.']
        masculine_titles = ['M', 'M.', 'MM.', 'MM', 'Messieurs']
        plural_titles = ['Mmes', 'MM.', 'MM', 'Messieurs']

        separator_RegEx = re.compile(r'\bet|'
                                     r',')
        # comma_RegEx = re.compile(r'\b,\b')
        details = {}

        for idx_r, r in enumerate(roles):

            detail_list = []
            key = roles_keys.get(r[0])
            # if they have used titles, our job is very easy
            ti_list = [m.span() for m in re.finditer(ti_RegEx, r[1])]
            # Are there several people with the same role?
            if len(ti_list) > 0:

                for ti_ in ti_list:
                    # body of the extracted record
                    body = r[1][
                           ti_[1] + 1:]  # I am using ti_[1]+1 to eliminate '.'s at the begging of names (when they have
                    # used MM instead of MM., for example.

                    # male or female?
                    gender = None
                    # what is the title?
                    title = r[1][ti_[0]:ti_[1]]

                    # set the gender
                    if title in feminine_titles:
                        gender = Gender.FEMALE
                    elif title in masculine_titles:
                        gender = Gender.MALE
                    else:
                        message = f"Undefined title: " + title
                        raise ValueError(message)

                    # Is it a plural title?
                    if title in plural_titles:
                        # I need to split the names, if they have used et or ','

                        if separator_RegEx.search(body) is not None:
                            all_names = body.split('et')
                        # just some stupid corner case in VD_FindInfo
                        # They write MM. (or Mmes) and then write the names and the roles until the gender changes!
                        else:
                            all_names = [body]
                        for name in all_names:
                            detail = {}
                            name = remove_special_characters(name)
                            detail['gender'] = gender
                            first_last_name(name, detail)
                            detail['full name'] = name
                            detail_list.append(detail)

                    else:
                        detail = {}
                        # do we have multiple people?
                        if separator_RegEx.search(body) is not None:
                            body = body[:separator_RegEx.search(body).span()[0]]  # body [: until next title's start]

                        body = remove_special_characters(body)

                        detail['gender'] = gender
                        first_last_name(body, detail)
                        detail['full name'] = body
                        detail_list.append(detail)

            else:
                # what we will write to the json
                body = r[1]
                separator_span_list = [m.span() for m in re.finditer(separator_RegEx, body)]
                sep_cnt = len(separator_span_list)
                if sep_cnt > 0:
                    all_names = []
                    # we have only one separator
                    if sep_cnt == 1:
                        span = separator_span_list[0]
                        all_names.append(body[:span[0] - 1])
                        all_names.append(body[span[1] + 1:])
                    else:
                        for idx, span in enumerate(separator_span_list):
                            # first person
                            if idx == 0:
                                all_names.append(body[: span[0] - 1])
                            # we are in the middle
                            elif 0 < idx < sep_cnt - 1:
                                all_names.append(body[separator_span_list[idx - 1][1] + 1: span[
                                                                                               0] - 1])
                                # end if prev separator to the start of current separator
                            # last person
                            else:
                                all_names.append(body[separator_span_list[idx - 1][1] + 1: span[
                                                                                               0] - 1])
                                # end if prev separator to the start of current separator
                                all_names.append(body[span[1] + 1:])  # end of this separator to the end
                else:
                    all_names = [body]
                for name in all_names:
                    detail = {}
                    name = remove_special_characters(name)
                    if r[2] is not None:
                        detail['gender'] = r[2]
                    else:
                        detail['gender'] = Gender.UNKNOWN
                    detail['full name'] = name
                    first_last_name(name, detail)
                    detail_list.append(detail)

            details[key] = detail_list
        return details

    # Here are the RegEx for finding different roles and titles in the composition
    # Regular expressions are evaluated from left to right. Do not touch the sequence unless you are sure about it!
    cm_start_RegEx = re.compile(r'[C,c]omposition|'
                                r'[C,c]ompos[é,e] |'
                                r'[P,p]r[é,e]sident(e)?( )?:|'
                                r'[P,p]r[é,e]sidence de|'
                                r'_ [J,j]uge( )?:|'
                                r'\. L[e,a] greffi[e,è]r(e)? :'
                                )
    # Find the end of the composition
    cm_end_RegEx = re.compile(r'(\*)+|'
                              r'[S|s]tatuant au complet|'
                              r'Art\. (.)+ CP')
    # president
    pr_RegEx = re.compile(r' [P,p]r[é,e]siden[t,c](e)?')
    # vice president
    vpr_RegEx = re.compile(r'vice-pr[é,e]sident(e)?')
    # assesseur                 assesseur
    as_RegEx = re.compile(r'[A,a]ssesseu[r|s](e)?(s)?')
    # greffier
    gr_RegEx = re.compile(r'[G,g]reffi[e,è]r(e)?')
    # juges
    ju_RegEx = re.compile(r'[J,j]uge(s)?')
    # juges assesseurs
    ju_as_RegEx = re.compile(r'[J,j]ug(e)?(s)? assesseu[r|s](e)?(s)?')
    # delegate judge
    ju_dl_RegEx = re.compile(r'[J,j]uge(s)? délégué(e)?(s)?')
    # juge suppléante
    juSup_RegEx = re.compile(r'[J,j]uge(s)? suppl[é,e]ant(e)?(s)?')
    # title
    ti_RegEx = re.compile(r'\bMme(\.)?\b|\bM(\.)?\b|\bMM(\.)?\b|Mlle(\.)?|Mme(s)?|Messieur(s)?')
    #############################################END OF SHOULD BE MOVED TO THE COURT COMPOSITION FILE
    paragraphs_by_section = {section: [] for section in Section}
    paragraphs = get_paragraphs(decision)
    # Currently, we search the whole decision for the following keywords: president, presidence, compose, composition

    composition_candidate = get_composition_candidates(paragraphs, cm_start_RegEx, cm_end_RegEx)

    # Uncomment to see the extraction results in plain txt file

    if composition_candidate is None or len(composition_candidate) == 0:
        # We write all the missed descisions to a file to take a closer look and improve the efficiency
        f = open("VD_FindInfo_missed_decisions.txt", "a")
        f.write('%s' % paragraphs)
        f.write('\n-------------------------------------------------------------\n')
        f.close()
        message = f"We have missed the judicial people for some decisions"
        raise ValueError(message)
    else:
        f = open("VD_FindInfo_headers.txt", "a")
        f.write('%s' % composition_candidate)
        f.write('\n-------------------------------------------------------------\n')
        f.close()
    # paragraphs_by_section[Section.HEADER] = composition_candidate
    role = extract_judicial_people(composition_candidate)
    details = extract_details(role)
    f = open("VD_FindInfo_details.txt", "a")
    f.write('%s' % composition_candidate)
    f.write('%s' % details)
    f.write('\n-------------------------------------------------------------\n')
    f.close()
    # paragraphs_by_section[Section.FACTS] = paragraphs
    # return paragraphs_by_section
    pass


def VD_Omni(decision: Union[bs4.BeautifulSoup, str], namespace: dict) -> Optional[Dict[Section, List[str]]]:
    def get_paragraphs(soup):
        """
        Get composition of the decision
        :param soup:
        :return:
        """
        # by some bruteforce I have found out that the html files in VD_Omni all have a single div with one of the
        # following classes:
        possible_main_div_classes = ["WordSection1", "Section1"]
        # Iterate over this list and find out the current decision is using which class type
        for main_div_class in possible_main_div_classes:

            div = soup.find_all("div", class_=main_div_class)
            if len(div) != 0:
                break
        # We expect to have only one main div
        assert len(div) == 1
        # If the divs is empty raise an error
        if len(div) == 0:
            message = f"The main div has an unseen class type"
            raise ValueError(message)
        paragraphs = []
        # paragraph = None
        for element in div:
            if isinstance(element, bs4.element.Tag):
                text = str(element.string)
                # This is a hack to also get tags which contain other tags such as links to BGEs
                if text.strip() == 'None':
                    text = element.get_text()
                paragraph = clean_text(text)
                if paragraph not in ['', ' ', None]:  # discard empty paragraphs
                    paragraphs.append(paragraph)
        return paragraphs

    def get_composition_candidates(paragraphs, cm_start_RegEx, cm_end_RegEx):

        composition_candidate = None

        for paragraph in paragraphs:

            cm_start_ = cm_start_RegEx.search(paragraph)

            # If we did not find the RegEx in the paragraph
            if cm_start_ is None:
                continue
            else:
                # cm_end.start() would be relative to cm_start_.start()
                cm_end = cm_end_RegEx.search(paragraph[cm_start_.end():])

                if cm_end is None:
                    continue
                else:
                    # we need to handle one stupid corner case
                    stupid_corner_case_RegEx = re.compile(r'juuuuujuujujujuges')
                    if stupid_corner_case_RegEx.search(paragraph) is not None:
                        continue
                    composition_candidate = paragraph[cm_start_.start():cm_start_.end() + cm_end.start()]
                break

            # Store all the compositions in a signle list

        return composition_candidate

    # paragraphs_by_section = {section: [] for section in Section}
    paragraphs = get_paragraphs(decision)

    # Currently, we search the whole decision for the following keywords: president, presidence, compose, composition
    cm_start_RegEx = re.compile(r'Composition de la section:|'
                                r'[C,c]omposition|'
                                r'[P,p]r[é,e]sident(e)?( )?:|'
                                r'[P,p]r[é,e]sidence de|'
                                r'compos[é,e](e)? de'
                                )
    # Find the end of the composition
    cm_end_RegEx = re.compile(r'[R,r][e,é]courant(e)?(s)?|'
                              r'[R,r]equ[é,e]rant(e)?(s)?|'
                              r'[V,v]u le(s)? fai[t|s](s)?|'
                              r'[V,v]u le(s)? recour(s)?|'
                              r'([C|c]onstate )?[E,e]n fait(s)?|'
                              r'[C,c]onsid[é,e]rant(e)? en droit|'
                              r'(\*)+|'
                              r' Vu l(es|a) décision(s)?|'
                              r'[L,l]e tribunal|'
                              r'Délibérant|'
                              r'La section des recours'
                              # r'(Vu)? ([E,e]n|les)? fait(s)? (suivant)? |'
                              )

    composition_candidate = get_composition_candidates(paragraphs, cm_start_RegEx, cm_end_RegEx)

    # Uncomment to see the extraction results in plain txt file

    if composition_candidate is None or len(composition_candidate) == 0:
        # We write all the missed descisions to a file to take a closer look and improve the efficiency
        f = open("VD_Omni_missed_decisions.txt", "a")
        f.write('%s' % paragraphs)
        f.write('\n-------------------------------------------------------------\n')
        f.close()
        message = f"We have missed the judicial people for some decisions"
        raise ValueError(message)
    else:
        f = open("VD_Omni_headers.txt", "a")
        f.write('%s' % composition_candidate)
        f.write('\n-------------------------------------------------------------\n')
        f.close()

    #############################################SHOULD BE MOVED TO THE COURT COMPOSITION FILE
    def find_the_keywords(candidate):
        """

                @param candidate: a string which should contain the judicial people @return: a dictionary with roles
                as keys and each value contains a tuple of 1)Boolean value indicating whether the role is available
                or not 2) the span of occurrence of the role's keyword
        """
        cm_start_available, cm_end_available, vpr_available, pr_available, as_available, gr_available, ju_available, ju_as_available, ju_su_available, ju_rp_available, ti_available = False, False, False, False, False, False, False, False, False, False, False
        cm_start_span, cm_end_span, vpr_span, pr_span, as_span, gr_span, ju_span, ju_as_span, ju_su_span, ju_rp_span, ti_span_list = None, None, None, None, None, None, None, None, None, None, None
        vpr_gender, pr_gender, as_gender, gr_gender, ju_gender, ju_as_gender, ju_su_gender, ju_rp_gender = None, None, None, None, None, None, None, None

        cm_start_ = cm_start_RegEx.search(candidate)
        cm_end_ = cm_end_RegEx.search(candidate)
        pr_ = pr_RegEx.search(candidate)
        vpr_ = vpr_RegEx.search(candidate)
        as_ = as_RegEx.search(candidate)
        gr_ = gr_RegEx.search(candidate)
        ju_ = ju_RegEx.search(candidate)
        ju_su_ = ju_sup_RegEx.search(candidate)
        ju_as_ = ju_as_RegEx.search(candidate)
        ju_rp_ = ju_rp_RegEx.search(candidate)
        ti_ = ti_RegEx.search(candidate)

        # we can find the gender by the gender of the role used. In french they add an extra 'e' or 'se' for feminine
        feminine_roles_RegEx = re.compile(r'[P,p]r[é,e]sidente|[A,a]ssesseu(re|se)|[G,g]reffi[e,è]re|'
                                          r'suppl[é,e]ant(e)|rapporteu(re|se)|La\b')
        masculine_roles_RegEx = re.compile(r'[P,p]r[é,e]sident(s)?\b|[A,a]ssesseur(s)?\b|[G,g]reffi[e,è]r(s)?\b|'
                                           r'suppl[é,e]ant\b|rapporteur\b|Le\b')

        if cm_start_ is not None:
            cm_start_available = True
            cm_start_span = cm_start_.span()

        if cm_end_ is not None:
            cm_end_available = True
            cm_end_span = cm_end_.span()

        if pr_ is not None:
            pr_available = True
            pr_span = pr_.span()
            if feminine_roles_RegEx.search(candidate[pr_span[0]:pr_span[1]]):
                pr_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[pr_span[0]:pr_span[1]]):
                pr_gender = Gender.MALE
            else:
                pr_gender = None

        if vpr_ is not None:
            vpr_available = True
            vpr_span = vpr_.span()
            if feminine_roles_RegEx.search(candidate[vpr_span[0]:vpr_span[1]]):
                vpr_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[vpr_span[0]:vpr_span[1]]):
                vpr_gender = Gender.MALE
            else:
                vpr_gender = None

        if as_ is not None:
            as_available = True
            as_span = as_.span()
            if feminine_roles_RegEx.search(candidate[as_span[0]:as_span[1]]):
                as_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[as_span[0]:as_span[1]]):
                as_gender = Gender.MALE
            else:
                as_gender = None

        if gr_ is not None:
            gr_available = True
            gr_span = gr_.span()
            if feminine_roles_RegEx.search(candidate[gr_span[0]:gr_span[1]]):
                gr_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[gr_span[0]:gr_span[1]]):
                gr_gender = Gender.MALE
            else:
                gr_gender = None

        if ju_ is not None:
            ju_available = True
            ju_span = ju_.span()
            if feminine_roles_RegEx.search(candidate[ju_span[0]:ju_span[1]]):
                ju_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[ju_span[0]:ju_span[1]]):
                ju_gender = Gender.MALE
            else:
                ju_gender = None

        if ju_su_ is not None:
            ju_su_available = True
            ju_su_span = ju_su_.span()
            if feminine_roles_RegEx.search(candidate[ju_su_span[0]:ju_su_span[1]]):
                ju_su_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[ju_su_span[0]:ju_su_span[1]]):
                ju_su_gender = Gender.MALE
            else:
                ju_su_gender = None

        if ju_as_ is not None:
            ju_as_available = True
            ju_as_span = ju_as_.span()
            if feminine_roles_RegEx.search(candidate[ju_as_span[0]:ju_as_span[1]]):
                ju_as_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[ju_as_span[0]:ju_as_span[1]]):
                ju_as_gender = Gender.MALE
            else:
                ju_as_gender = None

        if ju_rp_ is not None:
            ju_rp_available = True
            ju_rp_span = ju_rp_.span()
            if feminine_roles_RegEx.search(candidate[ju_rp_span[0]:ju_rp_span[1]]):
                ju_rp_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[ju_rp_span[0]:ju_rp_span[1]]):
                ju_rp_gender = Gender.MALE
            else:
                ju_rp_gender = None

        if ti_ is not None:
            ti_available = True
            ti_span_list = [m.span() for m in re.finditer(ti_RegEx, candidate)]

        # to handle the corner case when we have ju_su or ju_as or ju_rp but not the ju
        if ju_available and ju_as_available:
            if ju_span[0] == ju_as_span[0]:
                ju_available = False
        if ju_available and ju_su_available:
            if ju_span[0] == ju_su_span[0]:
                ju_available = False
        if ju_available and ju_rp_available:
            if ju_span[0] == ju_rp_span[0]:
                ju_available = False
        if ju_as_available and as_available:
            if ju_as_span[0] < as_span[0] and ju_as_span[1] >= as_span[1]:
                as_available = False

        keyword_dict = {
            'cm_start': [cm_start_available, cm_start_span],
            'cm_end': [cm_end_available, cm_end_span],
            'pr': [pr_available, pr_span, pr_gender],
            'vpr': [vpr_available, vpr_span, vpr_gender],
            'as': [as_available, as_span, as_gender],
            'gr': [gr_available, gr_span, gr_gender],
            'ju': [ju_available, ju_span, ju_gender],
            'ju_su': [ju_su_available, ju_su_span, ju_su_gender],
            'ju_as': [ju_as_available, ju_as_span, ju_as_gender],
            'ju_rp': [ju_rp_available, ju_rp_span, ju_rp_gender],
            'ti': [ti_available, ti_span_list]
        }
        return keyword_dict

    def eliminate_invalid_roles(keyword_dict):
        """

        @param keyword_dict: receives a dictionary with keys = role and values = tuples of bool (availability of the role)
        and the span of the keyword
        @return: returns a dictionary of roles whose availability field is True
        """
        invalid_roles = []
        for k, v in keyword_dict.items():
            # if a role is not found, mark it as invalid
            if not v[0]:
                invalid_roles.append(k)
        for k in invalid_roles:
            keyword_dict.pop(k)
        return keyword_dict

    def extraction_using_titles(ti_, candidate, keywords):
        """

        @param ti_: a list of title's span()
        @param candidate: a string which is potentially contains the composition
        @param keywords: a list of sorted roles and their span()
        @return:
        """
        roles = []

        idx_val = 0
        idx_title = 0
        prev_role = None
        next_role = None

        for val in keywords:

            if idx_val < len(keywords) - 1:
                next_role = keywords[idx_val + 1][1][1]

            if idx_title == len(ti_):
                print(candidate)
                print(keywords)
                print(roles)
                message = f"Extraction using title is not possible"
                raise ValueError(message)
            ti_e = ti_[idx_title]

            if prev_role is not None:
                # Several people have the same role
                while ti_e[0] < prev_role and idx_title < len(ti_) - 1:
                    # I should go to next title
                    idx_title += 1
                    ti_e = ti_[idx_title]
            # the person's name and title are mentioned before their roles
            if ti_e[0] < val[1][1][0]:
                roles.append([val[0], candidate[ti_e[0]:val[1][1][0]], val[1][2]])  # ti_start to role start
            # the person's name and title are mentioned after their roles
            else:
                # Is it the last item?
                if idx_val == len(keywords) - 1:
                    roles.append([val[0], candidate[val[1][1][1]:], val[1][2]])
                else:
                    # we are in the middle
                    if next_role is not None:
                        roles.append(
                            [val[0], candidate[ti_e[0]:next_role[0]], val[1][2]])  # ti_start to next_role_start
                    else:  # we should not end up here
                        assert False

            # we need to store the prev_role for cases when several people have the same role
            prev_role = val[1][1][0]
            # increase the indexes for next loop
            idx_val += 1
            idx_title += 1
        return roles

    def extraction_using_composition(cm_, candidate, keywords):
        """
        @param cm_: The output of cm_RegEx. We can call its span() method to find where it occurs in the string
        @param candidate: a 400-character string which potentially contains the composition
        @param keywords: a sorted list of roles and their span
        @return: A list of tuples whith 1)the role keyword 2) their details
        """
        roles = []
        idx_val = 0
        prev_role = None
        next_role = None
        # for role in keywords
        for val in keywords:
            # If we are not at the end, store the next role in next_role variable
            if idx_val != len(keywords) - 1:
                next_role = keywords[idx_val + 1]
            # if composition_end is within president_start+5 then names come after their roles
            if cm_[1][1] + 5 > val[1][1][0]:
                # if we are not at the end
                if idx_val != len(keywords) - 1:
                    roles.append(
                        [val[0], candidate[val[1][1][1]:next_role[1][1][0]],
                         val[1][2]])  # current_role_end to next_role_start
                # last person in the composition
                else:
                    roles.append([val[0], candidate[val[1][1][1]:], val[1][2]])
            # otherwise, the names appear before the keyword
            else:
                # we have just started
                if idx_val == 0:
                    roles.append(
                        [val[0], candidate[cm_[1][1]:val[1][1][0]], val[1][2]])  # composition_end to role_begin
                # if we are in between
                elif idx_val != len(keywords) - 1:
                    roles.append(
                        [val[0], candidate[prev_role[1][1][1]:val[1][1][0]],
                         val[1][2]])  # prev_role_end to current_role_start
                else:
                    # some times we have 'Greffiere: name'
                    if val[1][1][1] + 1 < len(candidate) and candidate[val[1][1][1] + 1] == ':':
                        roles.append([val[0], candidate[val[1][1][1]:], val[1][2]])
                    else:
                        roles.append(
                            [val[0], candidate[prev_role[1][1][1]:val[1][1][0]],
                             val[1][2]])  # prev_role_end to current_role_start

            # we need to store the prev_role for cases when one role has several titles
            prev_role = val
            # increase the indexes for next loop
            idx_val += 1
        return roles

    def extract_judicial_people(candidate):
        """

        @param candidates: the string candidates for compostion
        @return: a list of tuples with judicial people's 1) role 2)their details
        """

        # iterate over all the candidates

        # find all the keyword's occurance in the candidate
        keywords = find_the_keywords(candidate)
        # pop out composition, and titles
        cm_start_ = keywords.pop('cm_start')
        cm_end_ = keywords.pop('cm_end')
        ti_ = keywords.pop('ti')
        # it is vital to see if titles are used or not
        ti_available = ti_[0]
        ti_ = ti_[1]
        # preprocessing: eliminate those roles that were not found
        keywords = eliminate_invalid_roles(keywords)
        # preprocessing: sort the roles based on their order (which comes earlier?)
        sorted_keywords = sorted(keywords.items(), key=lambda e: e[1][1][0])

        # if decision is using the people titles
        if ti_available is not False and len(ti_) >= len(keywords.items()):

            role = extraction_using_titles(ti_, candidate, sorted_keywords)

        # if titles are not used or not everybody has a title
        else:
            # we may be able to extract people using the composition keyword
            if cm_start_[0]:
                role = extraction_using_composition(cm_start_, candidate, sorted_keywords)

            else:
                # we are in the middle
                if next_role is not None:
                    roles.append([val[0], candidate[ti_e[0]:next_role[0]]])  # ti_start to next_role_start
                else:  # we should not end up here
                    assert False
        return role

    def remove_special_characters(in_str):
        """

        @param in_str: Input string
        @return: output string without the following characters: {",",";","s:","e:","******"}
        """
        # for ch in characters_to_replace:
        in_str = in_str.replace(",", "")
        in_str = in_str.replace(";", "")
        # some times roles are female or plural
        in_str = in_str.replace("s:", "")
        in_str = in_str.replace("e:", "")
        # remove sequences of '*'
        star_RegEx = re.compile(r'\*+')
        star_ = star_RegEx.search(in_str)
        if star_ is not None:
            star_s = star_.span()
            in_str = in_str[:star_s[0] - 1] + in_str[star_s[1] + 1:]
        return in_str

    def first_last_name(full_name, detail):
        """

        @param full_name: A string that potentially contains: first name (or initials) and last name
        @param detail: a dictionary which contains the details of the judicial people
        @return: the detail dictionary with two new records: first name (or initials) and last name
        """
        dot_RegEx = re.compile(r'\w\.\b')
        dot_ = dot_RegEx.search(full_name)
        names = full_name.split(" ")
        last_name = False
        # remove all the empty strings or strings of length 1
        for idx, name in enumerate(names):
            if name == "" or len(name) == 1:
                names.pop(idx)
        for name in names:
            # is it intials?
            if dot_ is not None:
                detail['initials']: name
                last_name = True
            # is it the first or the last name?
            # In some decisions, we only have the last name
            elif len(names) > 1 and last_name == False:
                detail['first name'] = name
                last_name = True
            else:
                detail['last name'] = name
        return

    def extract_details(roles):
        """

        @param roles: a list of tuples with judicial people's 1) role 2) details
        @return: A dictionary ready to be written in the json file
        """
        roles_keys = {'pr': CourtRole.PRESIDENT, 'vpr': CourtRole.VICE_PRESIDENT, 'as': CourtRole.ASSESSOR,
                      'gr': CourtRole.CLERK, 'ju': CourtRole.JUDGE, 'ju_su': CourtRole.JUDGE_SUPPLEMENTARY,
                      'ju_rp': CourtRole.JUDGE_REPORTER, 'ju_dl': CourtRole.DELEGATE_JUDGE}
        feminine_titles = ['Mme', 'Mme.', 'Mmes', 'Mlle', 'Mlle.']
        masculine_titles = ['Messieur', 'M', 'M.', 'MM.', 'MM', 'Messieurs']
        plural_titles = ['Mmes', 'MM.', 'MM', 'Messieurs']
        separator_RegEx = re.compile(r'\bet|'
                                     r',')
        details = {}

        for idx_r, r in enumerate(roles):

            detail_list = []
            key = roles_keys.get(r[0])
            # if they have used titles, our job is very easy
            ti_list = [m.span() for m in re.finditer(ti_RegEx, r[1])]
            # Are there several people with the same role?
            if len(ti_list) > 0:

                for ti_ in ti_list:
                    # body of the extracted record
                    body = r[1][
                           ti_[1] + 1:]  # I am using ti_[1]+1 to eliminate '.'s at the begging of names (when they have
                    # used MM instead of MM., for example.

                    # male or female?
                    gender = None
                    # what is the title?
                    title = r[1][ti_[0]:ti_[1]]

                    # set the gender
                    if title in feminine_titles:
                        gender = Gender.FEMALE
                    elif title in masculine_titles:
                        gender = Gender.MALE
                    else:
                        message = f"Undefined title: " + title
                        raise ValueError(message)

                    # Is it a plural title?
                    if title in plural_titles:

                        # I need to split the names, if they have used et
                        if separator_RegEx.search(body) is not None:
                            all_names = body.split('et')
                        else:
                            all_names = [body]
                        for name in all_names:
                            detail = {}
                            name = remove_special_characters(name)
                            detail['gender'] = gender
                            first_last_name(name, detail)
                            detail['full name'] = name
                            detail_list.append(detail)

                    else:
                        detail = {}
                        # do we have multiple people?
                        if separator_RegEx.search(body) is not None:
                            body = body[:separator_RegEx.search(body).span()[0]]  # body [: until next title's start]

                        body = remove_special_characters(body)

                        detail['gender'] = gender
                        first_last_name(body, detail)
                        detail['full name'] = body
                        detail_list.append(detail)

            else:
                # what we will write to the json
                body = r[1]
                separator_span_list = [m.span() for m in re.finditer(separator_RegEx, body)]
                sep_cnt = len(separator_span_list)
                if sep_cnt > 0:
                    all_names = []
                    # we have only one separator
                    if sep_cnt == 1:
                        span = separator_span_list[0]
                        all_names.append(body[:span[0] - 1])
                        all_names.append(body[span[1] + 1:])
                    else:
                        for idx, span in enumerate(separator_span_list):
                            # first person
                            if idx == 0:
                                all_names.append(body[: span[0] - 1])
                            # we are in the middle
                            elif 0 < idx < sep_cnt - 1:
                                all_names.append(body[separator_span_list[idx - 1][1] + 1: span[
                                                                                               0] - 1])
                                # end if prev separator to the start of current separator
                            # last person
                            else:
                                all_names.append(body[separator_span_list[idx - 1][1] + 1: span[
                                                                                               0] - 1])
                                # end if prev separator to the start of current separator
                                all_names.append(body[span[1] + 1:])  # end of this separator to the end
                else:
                    all_names = [body]
                for name in all_names:
                    detail = {}
                    name = remove_special_characters(name)
                    if r[2] is not None:
                        detail['gender'] = r[2]
                    else:
                        detail['gender'] = Gender.UNKNOWN
                    detail['full name'] = name
                    first_last_name(name, detail)
                    detail_list.append(detail)

            details[key] = detail_list
        return details

    # Here are the RegEx for finding different roles and titles in the composition
    # composition
    cm_RegEx = re.compile(r'[C,c]omposition')
    # president
    pr_RegEx = re.compile(r'[P,p]r[é,e]siden[t,c](e)?')
    # vice president
    vpr_RegEx = re.compile(r'vice-pr[é,e]sident(e)?')
    # assesseur                  assesseurs
    as_RegEx = re.compile(r'[A,a]ssesseu(r|s)(e)?(s)?')
    # greffier
    gr_RegEx = re.compile(r'[G,g]reffi[e,è]r(e)?')
    # juges
    ju_RegEx = re.compile(r'[J,j]uge(s)?')
    # juge suppléante
    ju_sup_RegEx = re.compile(r'[J,j]uge(s)? suppl[é,e]ant(e)?')
    # juges assesseurs
    ju_as_RegEx = re.compile(r'[J,j]uge(s)? assesseu(r|se)(s)?')
    # juge rapporteur
    ju_rp_RegEx = re.compile(r'[J,j]uge(s)? rapporteur(e)?(s)?')
    # title
    ti_RegEx = re.compile(r'\bMme(\.)?\b|\bM(\.)?\b|\bMM(\.)?\b|Mlle(\.)?|Mme(s)?|Messieur(s)?')

    role = extract_judicial_people(composition_candidate)
    details = extract_details(role)
    f = open("VD_Omni_details.txt", "a")
    f.write('%s' % composition_candidate)
    f.write('%s' % details)
    f.write('\n-------------------------------------------------------------\n')
    f.close()
    #############################################END OF SHOULD BE MOVED TO THE COURT COMPOSITION FILE
    # paragraphs_by_section[Section.HEADER] = composition_candidate
    # paragraphs_by_section[Section.FACTS] = paragraphs
    # return paragraphs_by_section
    pass


def GE_Gerichte(decision: Union[bs4.BeautifulSoup, str], namespace: dict) -> Optional[Dict[Section, List[str]]]:


    def get_paragraphs(soup):

        """
        Get composition of the decision
        :param soup:
        :return:
        """

        divs = soup.find_all("div", class_=False)
        paragraphs = []

        # If no div is returned raise an error

        if len(divs) == 0:
            message = f"No div has been returned!"
            raise ValueError(message)
        for div in divs:
            paragraphs.append(clean_text(div.text))
        return paragraphs

    def get_composition_candidates(paragraphs, cm_start_RegEx, cm_end_RegEx):

        # did we miss composition of some of the decisions?

        composition_candidate = None

        for paragraph in paragraphs:

            cm_start_ = cm_start_RegEx.search(paragraph)

            # If we did not find the RegEx in the paragraph
            if cm_start_ is None:
                continue
            else:
                # cm_end.start() would be relatie to cm_start_.start()
                cm_end = cm_end_RegEx.search(paragraph[cm_start_.end():])

                if cm_end is None:
                    continue
                else:
                    # beacause cm_end.start() is relative
                    composition_candidate = paragraph[cm_start_.start():cm_start_.end() + cm_end.start()]
                break

            # Store all the compositions in a signle list

        return composition_candidate

    paragraphs_by_section = {section: [] for section in Section}
    paragraphs = get_paragraphs(decision)

    # Find the start of the composition

    cm_start_RegEx = re.compile(r'Si[é,e]geant(s)?|'
                                r'[A,a]u nom (de la|du) ([C,c]ommission)?([C,c]hambre)?([T,t]ribunal)? administrati(ve|f) :|'
                                r'L[a,e] [G,g]reffi[è,e]r(e)?|'
                                r'L[a,e] pr[é,e]sident(e)?( du Tribunal administratif)?( )?:|'
                                r'L[a,e] [V,v]ice-pr[é,e]sident(e)? :|'
                                r'ARR[Ê,E]T du (.)+ 20.. ')

    # Find the end of the composition
    cm_end_RegEx = re.compile(r'(Une )?[C,c]opie conforme|'
                              r'[V,v]oie(s)? de recours |'
                              r'La présente décision|'
                              r'Indication des voies de recours|'
                              r'S\'agissant de mesures superprovisionnelles|'
                              r'Par jugement du (..|.) (.)+ 20..(,| )|'
                              r'Les parties peuvent|'
                              r'Conformément aux art\.|'
                              r'EN FAIT |'
                              r'd’audience|'
                              r'le la greffi[è,e]re :|'
                              r'Au nom de la Commission de surveillance'
                              )
    # r'Au nom (de la|du) ([C,c]ommission)?([C,c]hambre)?([T,t]ribunal)?')

    composition_candidate = get_composition_candidates(paragraphs, cm_start_RegEx, cm_end_RegEx)

    if composition_candidate is None or len(composition_candidate) == 0:
        # We write all the missed descisions to a file to take a closer look and improve the efficiency
        f = open("GE_Gerichte_missed_decisions.txt", "a")
        f.write('%s' % paragraphs)
        f.write('\n-------------------------------------------------------------\n')
        f.close()
        message = f"We have missed the judicial people for some decisions"
        raise ValueError(message)
    else:
        f = open("GE_Gerichte_headers.txt", "a")
        f.write('%s' % composition_candidate)
        f.write('\n-------------------------------------------------------------\n')
        f.close()

    #############################################SHOULD BE MOVED TO THE COURT COMPOSITION FILE
    def find_the_keywords(candidate):
        """

                @param candidate: a string which should contain the judicial people @return: a dictionary with roles
                as keys and each value contains a tuple of 1)Boolean value indicating whether the role is available
                or not 2) the span of occurrence of the role's keyword
        """
        ad_available, cm_start_available, cm_end_available, vpr_available, pr_available, pr_si_available, as_available, gr_available, ju_available, ju_as_available, ju_su_available, ju_rp_available, ti_available = False, False, False, False, False, False, False, False, False, False, False, False, False
        ad_span, cm_start_span, cm_end_span, vpr_span, pr_span, pr_si_span, as_span, gr_span, ju_span, ju_as_span, ju_su_span, ju_rp_span, ti_span_list = None, None, None, None, None, None, None, None, None, None, None, None, None
        vpr_gender, pr_gender, pr_si_gender, as_gender, gr_gender, ju_gender, ju_as_gender, ju_su_gender, ju_rp_gender = None, None, None, None, None, None, None, None, None

        ad_ = ad_RegEx.search(candidate)
        cm_start_ = cm_start_RegEx.search(candidate)
        cm_end_ = cm_end_RegEx.search(candidate)
        pr_ = pr_RegEx.search(candidate)
        vpr_ = vpr_RegEx.search(candidate)
        pr_si_ = pr_si_RegEx.search(candidate)
        as_ = as_RegEx.search(candidate)
        gr_ = gr_RegEx.search(candidate)
        ju_ = ju_RegEx.search(candidate)
        ju_su_ = ju_sup_RegEx.search(candidate)
        ju_as_ = ju_as_RegEx.search(candidate)
        ju_rp_ = ju_rp_RegEx.search(candidate)
        ti_ = ti_RegEx.search(candidate)

        # we can find the gender by the gender of the role used. In french they add an extra 'e' or 'se' for feminine
        feminine_roles_RegEx = re.compile(r'[P,p]r[é,e]sidente|[A,a]ssesseu(re|se)|[G,g]reffi[e,è]re|'
                                          r'suppl[é,e]ant(e)|rapporteu(re|se)|La\b|la\b')
        masculine_roles_RegEx = re.compile(r'[P,p]r[é,e]sident\b|[A,a]ssesseur\b|[G,g]reffi[e,è]r\b|'
                                           r'suppl[é,e]ant\b|rapporteur\b|Le\b|le\b')

        if ad_ is not None:
            ad_available = True
            ad_span = ad_.span()

        if cm_start_ is not None:
            cm_start_available = True
            cm_start_span = cm_start_.span()

        if cm_end_ is not None:
            cm_end_available = True
            cm_end_span = cm_end_.span()

        if pr_ is not None:
            pr_available = True
            pr_span = pr_.span()

            if feminine_roles_RegEx.search(candidate[pr_span[0]:pr_span[1]]):
                pr_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[pr_span[0]:pr_span[1]]):
                pr_gender = Gender.MALE
            else:
                pr_gender = None

        if vpr_ is not None:
            vpr_available = True
            vpr_span = vpr_.span()
            if feminine_roles_RegEx.search(candidate[vpr_span[0]:vpr_span[1]]):
                vpr_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[vpr_span[0]:vpr_span[1]]):
                vpr_gender = Gender.MALE
            else:
                vpr_gender = None

        if pr_si_ is not None:
            pr_si_available = True
            pr_si_span = pr_si_.span()
            if feminine_roles_RegEx.search(candidate[pr_si_span[0]:pr_si_span[1]]):
                pr_si_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[pr_si_span[0]:pr_si_span[1]]):
                pr_si_gender = Gender.MALE
            else:
                pr_si_gender = None

        if as_ is not None:
            as_available = True
            as_span = as_.span()
            if feminine_roles_RegEx.search(candidate[as_span[0]:as_span[1]]):
                as_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[as_span[0]:as_span[1]]):
                as_gender = Gender.MALE
            else:
                as_gender = None
        if gr_ is not None:
            gr_available = True
            gr_span = gr_.span()
            if feminine_roles_RegEx.search(candidate[gr_span[0]:gr_span[1]]):
                gr_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[gr_span[0]:gr_span[1]]):
                gr_gender = Gender.MALE
            else:
                gr_gender = None
        if ju_ is not None:
            ju_available = True
            ju_span = ju_.span()
            if feminine_roles_RegEx.search(candidate[ju_span[0]:ju_span[1]]):
                ju_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[ju_span[0]:ju_span[1]]):
                ju_gender = Gender.MALE
            else:
                ju_gender = None

        if ju_su_ is not None:
            ju_su_available = True
            ju_su_span = ju_su_.span()
            if feminine_roles_RegEx.search(candidate[ju_su_span[0]:ju_su_span[1]]):
                ju_su_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[ju_su_span[0]:ju_su_span[1]]):
                ju_su_gender = Gender.MALE
            else:
                ju_su_gender = None
        if ju_as_ is not None:
            ju_as_available = True
            ju_as_span = ju_as_.span()
            if feminine_roles_RegEx.search(candidate[ju_as_span[0]:ju_as_span[1]]):
                ju_as_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[ju_as_span[0]:ju_as_span[1]]):
                ju_as_gender = Gender.MALE
            else:
                ju_as_gender = None
        if ju_rp_ is not None:
            ju_rp_available = True
            ju_rp_span = ju_rp_.span()
            if feminine_roles_RegEx.search(candidate[ju_rp_span[0]:ju_rp_span[1]]):
                ju_rp_gender = Gender.FEMALE
            elif masculine_roles_RegEx.search(candidate[ju_rp_span[0]:ju_rp_span[1]]):
                ju_rp_gender = Gender.MALE
            else:
                ju_rp_gender = None
        if ti_ is not None:
            ti_available = True
            ti_span_list = [m.span() for m in re.finditer(ti_RegEx, candidate)]

        # to handle the corner case when we have ju_su or ju_as or ju_rp but not the ju
        if ju_available and ju_as_available:
            if ju_span[0] == ju_as_span[0]:
                ju_available = False
        if ju_available and ju_su_available:
            if ju_span[0] == ju_su_span[0]:
                ju_available = False
        if ju_available and ju_rp_available:
            if ju_span[0] == ju_rp_span[0]:
                ju_available = False
        if pr_available and pr_si_available:
            if pr_span[0] == pr_si_span[0]:
                pr_available = False
        if ju_as_available and as_available:
            if ju_as_span[0] < as_span[0] and ju_as_span[1] >= as_span[1]:
                as_available = False

        keyword_dict = {
            'ad': [ad_available, ad_span],
            'cm_start': [cm_start_available, cm_start_span],
            'cm_end': [cm_end_available, cm_end_span],
            'pr': [pr_available, pr_span, pr_gender],
            'pr_si': [pr_si_available, pr_si_span, pr_si_gender],
            'vpr': [vpr_available, vpr_span, vpr_gender],
            'as': [as_available, as_span, as_gender],
            'gr': [gr_available, gr_span, gr_gender],
            'ju': [ju_available, ju_span, ju_gender],
            'ju_su': [ju_su_available, ju_su_span, ju_su_gender],
            'ju_as': [ju_as_available, ju_as_span, ju_as_gender],
            'ju_rp': [ju_rp_available, ju_rp_span, ju_rp_gender],
            'ti': [ti_available, ti_span_list]
        }
        return keyword_dict

    def eliminate_invalid_roles(keyword_dict):
        """

        @param keyword_dict: receives a dictionary with keys = role and values = tuples of bool (availability of the role)
        and the span of the keyword
        @return: returns a dictionary of roles whose availability field is True
        """
        invalid_roles = []
        for k, v in keyword_dict.items():
            # if a role is not found, mark it as invalid
            if not v[0]:
                invalid_roles.append(k)
        for k in invalid_roles:
            keyword_dict.pop(k)
        return keyword_dict

    def extraction_using_titles(ti_, tr_, candidate, keywords):
        """

        @param ti_: a list of title's span()
        @param candidate: a string which is potentially contains the composition
        @param keywords: a list of sorted roles and their span()
        @return:
        """
        roles = []

        idx_val = 0
        idx_title = 0
        prev_role = None
        next_role = None

        for val in keywords:

            if idx_val < len(keywords) - 1:
                next_role = keywords[idx_val + 1][1][1]

            # there is no 'Au nom de la chambre(Tribunal) administrative' in the composition
            if tr_[0] is False or val[1][1][0] < tr_[1][0]:
                if idx_title == len(ti_):
                    print(candidate)
                    print(keywords)
                    print(roles)
                    message = f"Extraction using title is not possible"
                    raise ValueError(message)
                ti_e = ti_[idx_title]

                if prev_role is not None:
                    # Several people have the same role
                    while ti_e[0] < prev_role and idx_title < len(ti_) - 1:
                        # I should go to next title
                        idx_title += 1
                        ti_e = ti_[idx_title]
                # we will just do the usual thing then
                # the person's name and title are mentioned before their roles
                if ti_e[0] < val[1][1][0]:
                    roles.append([val[0], candidate[ti_e[0]:val[1][1][0]], val[1][2]])  # ti_start to role start
                # the person's name and title are mentioned after their roles
                else:
                    # Is it the last item?
                    if idx_val == len(keywords) - 1:
                        roles.append([val[0], candidate[val[1][1][1]:], val[1][2]])
                    else:
                        # we are in the middle
                        if next_role is not None:
                            roles.append(
                                [val[0], candidate[ti_e[0]:next_role[0]], val[1][2]])  # ti_start to next_role_start
                        else:  # we should not end up here
                            assert False
            # we have a 'Au nom (de la|du) chambre(Tribunal) administrative' in between which changes the format
            # Before the tr_.start everything is of the form : 'name, role'
            # After the tr_.end everything is of form: 'role: name' and no title is used
            else:
                # print("got here!")
                # print(candidate)
                # print(keywords)
                # print(roles)
                # print(next_role)
                # print(prev_role)
                # print(tr_[0])

                # Is it the last item?
                if idx_val == len(keywords) - 1:
                    roles.append([val[0], candidate[val[1][1][1]:], val[1][2]])
                else:
                    # we are in the middle
                    if next_role is not None:
                        roles.append(
                            [val[0], candidate[val[1][1][1]:next_role[0]],
                             val[1][2]])  # ti_start to next_role_start
                    else:  # we should not end up here
                        assert False
            # we need to store the prev_role for cases when several people have the same role
            prev_role = val[1][1][0]
            # increase the indexes for next loop
            idx_val += 1
            idx_title += 1
        return roles

    def extraction_using_composition(cm_, candidate, keywords):
        """
        @param cm_: The output of cm_RegEx. We can call its span() method to find where it occurs in the string
        @param candidate: a 400-character string which potentially contains the composition
        @param keywords: a sorted list of roles and their span
        @return: A list of tuples whith 1)the role keyword 2) their details
        """
        roles = []
        idx_val = 0
        prev_role = None
        next_role = None
        # for role in keywords
        for val in keywords:
            # If we are not at the end, store the next role in next_role variable
            if idx_val != len(keywords) - 1:
                next_role = keywords[idx_val + 1]
            # if composition_end is within president_start+5 then names come after their roles
            if cm_[1][1] + 5 > val[1][1][0]:
                # if we are not at the end
                if idx_val != len(keywords) - 1:
                    roles.append(
                        [val[0], candidate[val[1][1][1]:next_role[1][1][0]],
                         val[1][2]])  # current_role_end to next_role_start
                # last person in the composition
                else:
                    roles.append([val[0], candidate[val[1][1][1]:], val[1][2]])
            # otherwise, the names appear before the keyword
            else:
                # we have just started
                if idx_val == 0:
                    roles.append(
                        [val[0], candidate[cm_[1][1]:val[1][1][0]], val[1][2]])  # composition_end to role_begin
                # if we are in between
                elif idx_val != len(keywords) - 1:
                    roles.append(
                        [val[0], candidate[prev_role[1][1][1]:val[1][1][0]],
                         val[1][2]])  # prev_role_end to current_role_start
                else:
                    # some times we have 'Greffiere: name'
                    if val[1][1][1] + 1 < len(candidate) and candidate[val[1][1][1] + 1] == ':':
                        roles.append([val[0], candidate[val[1][1][1]:], val[1][2]])
                    else:
                        roles.append(
                            [val[0], candidate[prev_role[1][1][1]:val[1][1][0]],
                             val[1][2]])  # prev_role_end to current_role_start

            # we need to store the prev_role for cases when one role has several titles
            prev_role = val
            # increase the indexes for next loop
            idx_val += 1
        return roles

    def extract_judicial_people(candidate):
        """

        @param candidates: the string candidates for compostion
        @return: a list of tuples with judicial people's 1) role 2)their details
        """

        # iterate over all the candidates

        # find all the keyword's occurance in the candidate
        keywords = find_the_keywords(candidate)
        # pop out composition, and titles
        ad_ = keywords.pop('ad')
        cm_start_ = keywords.pop('cm_start')
        cm_end_ = keywords.pop('cm_end')
        ti_ = keywords.pop('ti')
        # it is vital to see if titles are used or not
        ti_available = ti_[0]
        ti_ = ti_[1]
        # preprocessing: eliminate those roles that were not found
        keywords = eliminate_invalid_roles(keywords)
        # preprocessing: sort the roles based on their order (which comes earlier?)
        sorted_keywords = sorted(keywords.items(), key=lambda e: e[1][1][0])

        # if decision is using the people titles
        if ti_available is not False and len(ti_) >= len(keywords.items()):

            role = extraction_using_titles(ti_, ad_, candidate, sorted_keywords)

        # if titles are not used or not everybody has a title
        else:
            # we may be able to extract people using the composition keyword
            role = extraction_using_composition(cm_start_, candidate, sorted_keywords)
        return role

    def remove_special_characters(in_str):
        """

        @param in_str: Input string
        @return: output string without the following characters: {",",";","s:","e:","******"}
        """
        # for ch in characters_to_replace:
        in_str = in_str.replace(",", "")
        in_str = in_str.replace(";", "")
        # some times roles are female or plural
        in_str = in_str.replace("s:", "")
        in_str = in_str.replace("e:", "")
        # remove sequences of '*'
        star_RegEx = re.compile(r'\*+')
        star_ = star_RegEx.search(in_str)
        if star_ is not None:
            star_s = star_.span()
            in_str = in_str[:star_s[0] - 1] + in_str[star_s[1] + 1:]
        return in_str

    def first_last_name(full_name, detail):
        """

        @param full_name: A string that potentially contains: first name (or initials) and last name
        @param detail: a dictionary which contains the details of the judicial people
        @return: the detail dictionary with two new records: first name (or initials) and last name
        """
        dot_RegEx = re.compile(r'\w\.\b')
        dot_ = dot_RegEx.search(full_name)
        names = full_name.split(" ")
        last_name = False
        # remove all the empty strings or strings of length 1
        for idx, name in enumerate(names):
            if name == "" or len(name) == 1:
                names.pop(idx)
        for name in names:
            # is it intials?
            if dot_ is not None:
                detail['initials']: name
                last_name = True
            # is it the first or the last name?
            # In some decisions, we only have the last name
            elif len(names) > 1 and last_name == False:
                detail['first name'] = name
                last_name = True
            else:
                detail['last name'] = name
        return

    def extract_details(roles):
        """

        @param roles: a list of tuples with judicial people's 1) role 2) details
        @return: A dictionary ready to be written in the json file
        """
        roles_keys = {'pr': CourtRole.PRESIDENT,'pr_si': CourtRole.PRESIDENT, 'vpr': CourtRole.VICE_PRESIDENT, 'as': CourtRole.ASSESSOR,
                      'gr': CourtRole.CLERK, 'ju': CourtRole.JUDGE, 'ju_su': CourtRole.JUDGE_SUPPLEMENTARY,
                      'ju_rp': CourtRole.JUDGE_REPORTER, 'ju_dl': CourtRole.DELEGATE_JUDGE,
                      'ju_as': CourtRole.JUDGE_ASSESSOR}
        feminine_titles = ['Mme', 'Mme.', 'Mmes', 'Mlle', 'Mlle.', 'Madame', 'Mesdames']
        masculine_titles = ['Messieur', 'M', 'M.', 'MM.', 'MM', 'Messieurs', 'Monsieur']
        plural_titles = ['Mmes', 'MM.', 'MM', 'Messieurs', 'Mesdames']
        separator_RegEx = re.compile(r'\bet|'
                                     r',')
        details = {}

        for idx_r, r in enumerate(roles):

            detail_list = []
            key = roles_keys.get(r[0])
            # if they have used titles, our job is very easy
            ti_list = [m.span() for m in re.finditer(ti_RegEx, r[1])]
            # Are there several people with the same role?
            if len(ti_list) > 0:

                for ti_ in ti_list:
                    # body of the extracted record
                    body = r[1][
                           ti_[1] + 1:]  # I am using ti_[1]+1 to eliminate '.'s at the begging of names (when they have
                    # used MM instead of MM., for example.

                    # male or female?
                    gender = None
                    # what is the title?
                    title = r[1][ti_[0]:ti_[1]]

                    # set the gender
                    if title in feminine_titles:
                        gender = Gender.FEMALE
                    elif title in masculine_titles:
                        gender = Gender.MALE
                    else:
                        message = f"Undefined title: " + title
                        raise ValueError(message)

                    # Is it a plural title?
                    if title in plural_titles:

                        # I need to split the names, if they have used et
                        if separator_RegEx.search(body) is not None:
                            all_names = body.split('et')
                        else:
                            all_names = [body]
                        for name in all_names:
                            detail = {}
                            name = remove_special_characters(name)
                            detail['gender'] = gender
                            first_last_name(name, detail)
                            detail['full name'] = name
                            detail_list.append(detail)
                    else:
                        detail = {}
                        # do we have multiple people?
                        if separator_RegEx.search(body) is not None:
                            body = body[:separator_RegEx.search(body).span()[0]]  # body [: until next title's start]

                        body = remove_special_characters(body)

                        detail['gender'] = gender
                        first_last_name(body, detail)
                        detail['full name'] = body
                        detail_list.append(detail)
            else:
                # what we will write to the json
                body = r[1]
                separator_span_list = [m.span() for m in re.finditer(separator_RegEx, body)]
                sep_cnt = len(separator_span_list)
                if sep_cnt > 0:
                    all_names = []
                    # we have only one separator
                    if sep_cnt == 1:
                        span = separator_span_list[0]
                        all_names.append(body[:span[0] - 1])
                        all_names.append(body[span[1] + 1:])
                    else:
                        for idx, span in enumerate(separator_span_list):
                            # first person
                            if idx == 0:
                                all_names.append(body[: span[0] - 1])
                            # we are in the middle
                            elif 0 < idx < sep_cnt - 1:
                                all_names.append(body[separator_span_list[idx - 1][1] + 1: span[

                                                                                               0] - 1])
                                # end if prev separator to the start of current separator
                            # last person
                            else:
                                all_names.append(body[separator_span_list[idx - 1][1] + 1: span[
                                                                                               0] - 1])
                                # end if prev separator to the start of current separator
                                all_names.append(body[span[1] + 1:])  # end of this separator to the end
                else:
                    all_names = [body]
                for name in all_names:
                    detail = {}
                    name = remove_special_characters(name)
                    if r[2] is not None:
                        detail['gender'] = r[2]
                    else:
                        detail['gender'] = Gender.UNKNOWN
                    detail['full name'] = name
                    first_last_name(name, detail)
                    detail_list.append(detail)
            details[key] = detail_list

        return details

    # Here are the RegEx for finding different roles and titles in the composition
    # In GE some times 'Au nom du Tribunal administratif' happens in between and changes the structure
    #
    ad_RegEx = re.compile(r'[A,a]u nom d[u,e]( la)? ([T,t]ribunal)?(chambre)? administrati(f|ve)')

    # president
    pr_RegEx = re.compile(r'(La|la|Le|le)? [P,p]r[é,e]sident(e)?( )?(:)?')
    # vice president
    vpr_RegEx = re.compile(r'(La|la|Le|le)? vice-pr[é,e]sident(e)?( )?(:)?')
    # le président siégeant      la présidente siégeant
    pr_si_RegEx = re.compile(r'(La|la|Le|le)? [P,p]r[é,e]sident(e)? si[é,e]geant(e)?( )?(:)?')
    # assesseur
    as_RegEx = re.compile(r'(La|la|Le|le)? [A,a]ssesseu(r|se)( )?(:)?')
    # greffier
    gr_RegEx = re.compile(r'(La|la|Le|le)? [G,g]reffi[e,è]r(e)?(-juriste)?( )?(:)?')
    # juges
    ju_RegEx = re.compile(r'(La|la|Le|le)?(.)? [J,j]uge(s)?( salariés)?( )?(:)?')
    # juge suppléante
    ju_sup_RegEx = re.compile(r'(La|la|Le|le)?(.)? [J,j]uge suppl[é,e]ant(e)?( )?(:)?')
    # juges assesseurs
    ju_as_RegEx = re.compile(r'(La|la|Le|le)?(.)? [J,j]ug(e)?(s)? assesseur(s)?( )?(:)?')
    # juge rapporteur
    ju_rp_RegEx = re.compile(r'(La|la|Le|le)?(.)? [J,j]uge rapporteu(se|re)?( )?(:)?')
    # title
    ti_RegEx = re.compile(
        r'\bMme(\.)?\b|\bM(\.)?\b|\bMM(\.)?\b|Mlle(\.)?|Mme(s)?|Messieur(s)?|Madame(s)?|Monsieur|Mesdames')

    role = extract_judicial_people(composition_candidate)
    details = extract_details(role)
    f = open("GE_Gerichte_details.txt", "a")
    f.write('%s' % composition_candidate)
    f.write('%s' % details)
    f.write('\n-------------------------------------------------------------\n')
    f.close()
    #############################################END OF SHOULD BE MOVED TO THE COURT COMPOSITION FILE
    # Uncomment to see the extraction results in plain txt file
    # paragraphs_by_section[Section.HEADER] = composition_candidate
    # paragraphs_by_section[Section.FACTS] = paragraphs
    # return paragraphs_by_section
    pass


def JU_Gerichte(decision: Union[bs4.BeautifulSoup, str], namespace: dict) -> Optional[Dict[Section, List[str]]]:
    def get_paragraphs(soup):

        """
        Get composition of the decision
        :param soup:
        :return:
        """

        return [clean_text(decision)]

    def get_composition_candidates(paragraphs, cm_start_RegEx, cm_end_RegEx):

        # did we miss composition of some of the decisions?

        composition_candidate = None

        for paragraph in paragraphs:

            cm_start_ = cm_start_RegEx.search(paragraph)

            # If we did not find the RegEx in the paragraph
            if cm_start_ is None:
                continue
            else:
                # cm_end.start() would be relative to cm_start_.start()
                cm_end_ = cm_end_RegEx.search(paragraph[cm_start_.end():])

                if cm_end_ is None:
                    continue
                else:
                    # beacause cm_end.start() is relative
                    composition_candidate = paragraph[cm_start_.start():cm_start_.end() + cm_end_.start()]
                break

            # Store all the compositions in a single list
        return composition_candidate

    paragraphs_by_section = {section: [] for section in Section}
    paragraphs = get_paragraphs(decision)

    # Find the start of the composition

    cm_start_RegEx = re.compile(r'[P,p]r[é,e]sident(-)?(e)?(.)?( )?:|'
                                r'[P,p]r[é,e]sident(e)? (a\.h(\.)?|e.o.|e.r.)?( )?:|'
                                r'Juge (pénal|civile)?( )?:'
                                )

    # Find the end of the composition
    cm_end_RegEx = re.compile(r'D[É,E]CISION( DU)?|'
                              r'ARR[E,Ê]T( DU)?|'
                              r'JUGEMENT( DU)?|'
                              r'ORDONNANCE( DU)?|'
                              r'MOTIFS DE LA DECISION RENDUE|'
                              r'CONSID[E,É]RANTS( DU)?'
                              )

    composition_candidate = get_composition_candidates(paragraphs, cm_start_RegEx, cm_end_RegEx)

    # Uncomment to receive the missed decisions and extracted compositions in seperate txt files
    if composition_candidate is None or len(composition_candidate) == 0:
        # We write all the missed descisions to a file to take a closer look and improve the efficiency
        f = open("JU_Gerichte_missed_decisions.txt", "a")
        f.write('%s' % paragraphs)
        f.write('\n-------------------------------------------------------------\n')
        f.close()
        message = f"We have missed the judicial people for some decisions"
        raise ValueError(message)
    else:
        f = open("JU_Gerichte_headers.txt", "a")
        f.write('%s' % composition_candidate)
        f.write('\n-------------------------------------------------------------\n')
        f.close()

    #############################################SHOULD BE MOVED TO THE COURT COMPOSITION FILE
    def find_the_keywords(candidate):
        """

                @param candidate: a string which should contain the judicial people @return: a dictionary with roles
                as keys and each value contains a tuple of 1)Boolean value indicating whether the role is available
                or not 2) the span of occurrence of the role's keyword 3) Gender of the roles
        """

        vpr_available, pr_available, pr_si_available, as_available, gr_available, ju_available, ju_as_available, ju_su_available, ju_rp_available, ti_available = False, False, False, False, False, False, False, False, False, False

        vpr_span, pr_span, pr_si_span, as_span, gr_span, ju_span, ju_as_span, ju_su_span, ju_rp_span = None, None, None, None, None, None, None, None, None

        vpr_gender, pr_gender, pr_si_gender, as_gender, gr_gender, ju_gender, ju_as_gender, ju_su_gender, ju_rp_gender = None, None, None, None, None, None, None, None, None

        pr_ = pr_RegEx.search(candidate)
        vpr_ = vpr_RegEx.search(candidate)
        pr_si_ = pr_si_RegEx.search(candidate)
        as_ = as_RegEx.search(candidate)
        gr_ = gr_RegEx.search(candidate)
        ju_ = ju_RegEx.search(candidate)
        ju_su_ = ju_sup_RegEx.search(candidate)
        ju_as_ = ju_as_RegEx.search(candidate)
        ju_rp_ = ju_rp_RegEx.search(candidate)

        # we can find the gender by the gender of the role used. In french they add an extra 'e' or 'se' for feminine
        feminine_roles_RegEx = re.compile(r'[P,p]r[é,e]sidente|[A,a]ssesseu(re|se)|[G,g]reffi[e,è]re|'
                                          r'suppl[é,e]ant(e)|rapporteu(re|se)')

        if pr_ is not None:
            pr_available = True
            pr_span = pr_.span()
            if feminine_roles_RegEx.search(candidate[pr_span[0]:pr_span[1]]) is not None:
                pr_gender = Gender.FEMALE
            else:
                pr_gender = Gender.MALE

        if vpr_ is not None:
            vpr_available = True
            vpr_span = vpr_.span()
            if feminine_roles_RegEx.search(candidate[vpr_span[0]:vpr_span[1]]) is not None:
                vpr_gender = Gender.FEMALE
            else:
                vpr_gender = Gender.MALE

        if pr_si_ is not None:
            pr_si_available = True
            pr_si_span = pr_si_.span()
            if feminine_roles_RegEx.search(candidate[pr_si_span[0]:pr_si_span[1]]) is not None:
                pr_si_gender = Gender.FEMALE
            else:
                as_gender = Gender.MALE

        if as_ is not None:
            as_available = True
            as_span = as_.span()
            if feminine_roles_RegEx.search(candidate[as_span[0]:as_span[1]]) is not None:
                as_gender = Gender.FEMALE
            else:
                as_gender = Gender.MALE

        if gr_ is not None:
            gr_available = True
            gr_span = gr_.span()
            if feminine_roles_RegEx.search(candidate[gr_span[0]:gr_span[1]]) is not None:
                gr_gender = Gender.FEMALE
            else:
                gr_gender = Gender.MALE

        if ju_ is not None:
            ju_available = True
            ju_span = ju_.span()
            ju_gender = Gender.UNKNOWN

        if ju_su_ is not None:
            ju_su_available = True
            ju_su_span = ju_su_.span()
            if feminine_roles_RegEx.search(candidate[ju_su_span[0]:ju_su_span[1]]) is not None:
                ju_su_gender = Gender.FEMALE
            else:
                ju_su_gender = Gender.MALE

        if ju_as_ is not None:
            ju_as_available = True
            ju_as_span = ju_as_.span()
            if feminine_roles_RegEx.search(candidate[ju_as_span[0]:ju_as_span[1]]) is not None:
                ju_as_gender = Gender.FEMALE
            else:
                ju_as_gender = Gender.MALE

        if ju_rp_ is not None:
            ju_rp_available = True
            ju_rp_span = ju_rp_.span()
            if feminine_roles_RegEx.search(candidate[ju_rp_span[0]:ju_rp_span[1]]) is not None:
                ju_rp_gender = Gender.FEMALE
            else:
                ju_rp_gender = Gender.MALE

        # to handle the corner case when we have ju_su or ju_as or ju_rp but not the ju
        if ju_available and ju_as_available:
            if ju_span[0] == ju_as_span[0]:
                ju_available = False
        if ju_available and ju_su_available:
            if ju_span[0] == ju_su_span[0]:
                ju_available = False
        if ju_available and ju_rp_available:
            if ju_span[0] == ju_rp_span[0]:
                ju_available = False
        if pr_available and pr_si_available:
            if pr_span[0] == pr_si_span[0]:
                pr_available = False

        keyword_dict = {
            'pr': [pr_available, pr_span, pr_gender],
            'pr_si': [pr_si_available, pr_si_span, pr_si_gender],
            'vpr': [vpr_available, vpr_span, vpr_gender],
            'as': [as_available, as_span, as_gender],
            'gr': [gr_available, gr_span, gr_gender],
            'ju': [ju_available, ju_span, ju_gender],
            'ju_su': [ju_su_available, ju_su_span, ju_su_gender],
            'ju_as': [ju_as_available, ju_as_span, ju_as_gender],
            'ju_rp': [ju_rp_available, ju_rp_span, ju_rp_gender]
        }
        return keyword_dict

    def eliminate_invalid_roles(keyword_dict):
        """

        @param keyword_dict: receives a dictionary with keys = role and values = tuples of bool (availability of the role)
        and the span of the keyword
        @return: returns a dictionary of roles whose availability field is True
        """
        invalid_roles = []
        for k, v in keyword_dict.items():
            # if a role is not found, mark it as invalid
            if not v[0]:
                invalid_roles.append(k)
        for k in invalid_roles:
            keyword_dict.pop(k)
        return keyword_dict

    def extract_judicial_people(candidate):
        """

        @param candidate: the string candidates for compostion
        @return: a list of tuples with judicial people's 1) role 2)their details
        """

        # find all the keyword's occurrence in the candidate
        keywords = find_the_keywords(candidate)

        # preprocessing: eliminate those roles that were not found
        keywords = eliminate_invalid_roles(keywords)
        # preprocessing: sort the roles based on their order (which comes earlier?)
        sorted_keywords = sorted(keywords.items(), key=lambda e: e[1][1][0])

        roles = []
        idx_val = 0
        next_role = None
        # for role in keywords
        for val in sorted_keywords:

            # If we are not at the end, store the next role in next_role variable
            if idx_val != len(sorted_keywords) - 1:
                next_role = sorted_keywords[idx_val + 1]
            # if we are not at the end
            if idx_val != len(sorted_keywords) - 1:
                roles.append(
                    [val[0], candidate[val[1][1][1]:next_role[1][1][0]],
                     val[1][2]])  # current_role_end to next_role_start
            # last person in the composition
            else:
                roles.append([val[0], candidate[val[1][1][1]:], val[1][2]])  # current_role_end to end
            # increase the indexes for next loop
            idx_val += 1

        return roles

    def remove_special_characters(in_str):
        """

        @param in_str: Input string
        @return: output string without the following characters: {",",";","s:","e:","******"}
        """
        # for ch in characters_to_replace:
        in_str = in_str.replace(",", "")
        in_str = in_str.replace(";", "")
        # some times roles are female or plural
        in_str = in_str.replace("s:", "")
        in_str = in_str.replace("e:", "")
        # remove sequences of '*'
        star_RegEx = re.compile(r'\*+')
        star_ = star_RegEx.search(in_str)
        if star_ is not None:
            star_s = star_.span()
            in_str = in_str[:star_s[0] - 1] + in_str[star_s[1] + 1:]
        return in_str

    def first_last_name(full_name, detail):
        """

        @param full_name: A string that potentially contains: first name (or initials) and last name
        @param detail: a dictionary which contains the details of the judicial people
        @return: the detail dictionary with two new records: first name (or initials) and last name
        """
        dot_RegEx = re.compile(r'\w\.\b')
        dot_ = dot_RegEx.search(full_name)
        names = full_name.split(" ")
        last_name = False
        # remove all the empty strings or strings of length 1
        for idx, name in enumerate(names):
            if name == "" or len(name) == 1:
                names.pop(idx)
        for name in names:
            # is it intials?
            if (dot_ is not None):
                detail['initials']: name
                last_name = True
            # is it the first or the last name?
            # In some decisions, we only have the last name
            elif (len(names) > 1 and last_name == False):
                detail['first name'] = name
                last_name = True
            else:
                detail['last name'] = name
        return

    def extract_details(roles):
        """

        @param roles: a list of tuples with judicial people's 1) role 2) details
        @return: A dictionary ready to be written in the json file
        """
        roles_keys = {'pr': CourtRole.PRESIDENT, 'vpr': CourtRole.VICE_PRESIDENT, 'as': CourtRole.ASSESSOR,
                      'gr': CourtRole.CLERK, 'ju': CourtRole.JUDGE, 'ju_su': CourtRole.JUDGE_SUPPLEMENTARY,
                      'ju_rp': CourtRole.JUDGE_REPORTER, 'ju_dl': CourtRole.DELEGATE_JUDGE,
                      'ju_as': CourtRole.JUDGE_ASSESSOR}

        separator_RegEx = re.compile(r'\bet|'
                                     r',')
        details = {}

        for idx_r, r in enumerate(roles):

            detail_list = []
            key = roles_keys.get(r[0])

            body = r[1]
            separator_span_list = [m.span() for m in re.finditer(separator_RegEx, body)]
            sep_cnt = len(separator_span_list)
            if sep_cnt > 0:
                all_names = []
                # we have only one separator
                if sep_cnt == 1:
                    span = separator_span_list[0]
                    all_names.append(body[:span[0] - 1])
                    all_names.append(body[span[1] + 1:])
                else:
                    for idx, span in enumerate(separator_span_list):
                        # first person
                        if idx == 0:
                            all_names.append(body[: span[0] - 1])
                        # we are in the middle
                        elif 0 < idx < sep_cnt - 1:
                            all_names.append(body[separator_span_list[idx - 1][1] + 1: span[
                                                                                           0] - 1])
                            # end if prev separator to the start of current separator
                        # last person
                        else:
                            all_names.append(body[separator_span_list[idx - 1][1] + 1: span[
                                                                                           0] - 1])
                            # end if prev separator to the start of current separator
                            all_names.append(body[span[1] + 1:])  # end of this separator to the end
            else:
                all_names = [body]
            for name in all_names:
                detail = {}
                name = remove_special_characters(name)
                if r[2] is not None:
                    detail['gender'] = r[2]
                else:
                    detail['gender'] = Gender.UNKNOWN
                detail['full name'] = name
                first_last_name(name, detail)
                detail_list.append(detail)
            details[key] = detail_list
        return details

    # Here are the RegEx for finding different roles and titles in the composition

    # president
    pr_RegEx = re.compile(r'[P,p]r[é,e]sident(e)? (a\.h(\.)?|e.o.|e.r.)?( )?:')
    # vice president
    vpr_RegEx = re.compile(r'vice-pr[é,e]sident(e)?( )? :')
    # le président siégeant
    pr_si_RegEx = re.compile(r'[P,]pr[é,e]sident si[é,e]geant(e)?( )?:')
    # assesseur
    as_RegEx = re.compile(r'[A,a]ssesseu(r|se)?( )?:')
    # greffier
    gr_RegEx = re.compile(r'[G,g]reffi[e,è]r(e)?( e\.r(\.)?)?( )?:')
    # juges
    ju_RegEx = re.compile(r'[J,j]uge(s)?()?(pénal|civile)?( )?:')
    # juge suppléante
    ju_sup_RegEx = re.compile(r'[J,j]uge suppl[é,e]ant(e)?(s)?( )?:')
    # juges assesseurs
    ju_as_RegEx = re.compile(r'[J,j]uge(s)? assesseur(s)?( )?:')
    # juge rapporteur
    ju_rp_RegEx = re.compile(r'[J,j]ug(e)? rapporteu[r|s](e)?( )?:')

    role = extract_judicial_people(composition_candidate)
    details = extract_details(role)
    # Uncomment to receive details in txt file
    f = open("JU_Gerichte_details.txt", "a")
    f.write('%s' % composition_candidate)
    f.write('%s' % details)
    f.write('\n-------------------------------------------------------------\n')
    f.close()
    #############################################END OF SHOULD BE MOVED TO THE COURT COMPOSITION FILE
    # Uncomment to see the extraction results in plain txt file
    # paragraphs_by_section[Section.HEADER] = composition_candidate
    # paragraphs_by_section[Section.FACTS] = paragraphs
    # return paragraphs_by_section
    pass



def CH_WEKO(decision: Union[bs4.BeautifulSoup, str], namespace: dict) -> Optional[Dict[Section, List[str]]]:

    if namespace['language'] == Language.FR:
        print("french decision found in CH_WEKO")
        f = open("CH_WEKO_soup.txt", "a")
        f.write('%s' % decision)
        f.write('\n-------------------------------------------------------------\n')
        f.close()
    pass
def CH_VB(decision: Union[bs4.BeautifulSoup, str], namespace: dict) -> Optional[Dict[Section, List[str]]]:

    if namespace['language'] == Language.FR:
        print("french decision found in CH_VB")
        f = open("CH_VB_soup.txt", "a")
        f.write('%s' % decision)
        f.write('\n-------------------------------------------------------------\n')
        f.close()
    pass
def CH_BVGer(decision: Union[bs4.BeautifulSoup, str], namespace: dict) -> Optional[Dict[Section, List[str]]]:

    if namespace['language'] == Language.FR:
        print("french decision found in CH_BVGer")
        f = open("CH_BVGer_soup.txt", "a")
        f.write('%s' % decision)
        f.write('\n-------------------------------------------------------------\n')
        f.close()
    pass

def CH_BSTG(decision: Union[bs4.BeautifulSoup, str], namespace: dict) -> Optional[Dict[Section, List[str]]]:

    if namespace['language'] == Language.FR:
        print("french decision found in CH_BSTG")
        f = open("CH_BSTG_soup.txt", "a")
        f.write('%s' % decision)
        f.write('\n-------------------------------------------------------------\n')
        f.close()
    pass

def CH_BPatG(decision: Union[bs4.BeautifulSoup, str], namespace: dict) -> Optional[Dict[Section, List[str]]]:

    if namespace['language'] == Language.FR:
        print("french decision found in CH_BPatG")
        f = open("CH_BPatG_soup.txt", "a")
        f.write('%s' % decision)
        f.write('\n-------------------------------------------------------------\n')
        f.close()
    pass
def CH_BGE(decision: Union[bs4.BeautifulSoup, str], namespace: dict) -> Optional[Dict[Section, List[str]]]:

    if namespace['language'] == Language.FR:
        print("french decision found in CH_BGE")
        f = open("CH_BGE_soup.txt", "a")
        f.write('%s' % decision)
        f.write('\n-------------------------------------------------------------\n')
        f.close()
    pass

def BS_Omni(decision: Union[bs4.BeautifulSoup, str], namespace: dict) -> Optional[Dict[Section, List[str]]]:
    """
    :param decision:    the decision parsed by bs4 or the string extracted of the pdf
    :param namespace:   the namespace containing some metadata of the court decision
    :return:            the sections dict (keys: section, values: list of paragraphs)
    """
    # As soon as one of the strings in the list (regexes) is encountered we switch to the corresponding section (key)
    # (?:C|c) is much faster for case insensitivity than [Cc] or (?i)c
    all_section_markers = {
        Language.DE: {
            Section.FACTS: [r'^Sachverhalt:?\s*$', r'^Tatsachen$'],
            Section.CONSIDERATIONS: [r'^Begründung:\s*$', r'Erwägung(en)?:?\s*$', r'^Entscheidungsgründe$',
                                     r'[iI]n Erwägung[:,]?\s*$'],
            Section.RULINGS: [r'Demgemäss erkennt d[\w]{2}', r'erkennt d[\w]{2} [A-Z]\w+:',
                              r'Appellationsgericht (\w+ )?(\(\w+\) )?erkennt', r'^und erkennt:$', r'erkennt:\s*$'],
            Section.FOOTER: [r'^Rechtsmittelbelehrung$',
                             r'AUFSICHTSKOMMISSION', r'APPELLATIONSGERICHT']
        }
    }
    valid_namespace(namespace, all_section_markers)

    section_markers = prepare_section_markers(all_section_markers, namespace)

    divs = decision.find_all(
        "div", class_=['WordSection1', 'Section1', 'WordSection2'])
    paragraphs = get_paragraphs(divs)
    return associate_sections(paragraphs, section_markers, namespace)


def CH_BGer(decision: Union[bs4.BeautifulSoup, str], namespace: dict) -> Optional[Dict[Section, List[str]]]:
    """
    :param decision:    the decision parsed by bs4 or the string extracted of the pdf
    :param namespace:   the namespace containing some metadata of the court decision
    :return:            the sections dict (keys: section, values: list of paragraphs)
    """

    # As soon as one of the strings in the list (regexes) is encountered we switch to the corresponding section (key)
    # (?:C|c) is much faster for case insensitivity than [Cc] or (?i)c
    all_section_markers = {
        Language.DE: {
            # "header" has no markers!
            # at some later point we can still divide rubrum into more fine-grained sections like title, judges, parties, topic
            # "title": ['Urteil vom', 'Beschluss vom', 'Entscheid vom'],
            # "judges": ['Besetzung', 'Es wirken mit', 'Bundesrichter'],
            # "parties": ['Parteien', 'Verfahrensbeteiligte', 'In Sachen'],
            # "topic": ['Gegenstand', 'betreffend'],
            Section.FACTS: [r'Sachverhalt:', r'hat sich ergeben', r'Nach Einsicht', r'A\.-'],
            Section.CONSIDERATIONS: [r'Erwägung:', r'[Ii]n Erwägung', r'Erwägungen:'],
            Section.RULINGS: [r'erkennt d[\w]{2} Präsident', r'Demnach (erkennt|beschliesst)', r'beschliesst.*:\s*$',
                              r'verfügt(\s[\wäöü]*){0,3}:\s*$', r'erk[ae]nnt(\s[\wäöü]*){0,3}:\s*$',
                              r'Demnach verfügt[^e]'],
            Section.FOOTER: [
                r'^[\-\s\w\(]*,( den| vom)?\s\d?\d\.?\s?(?:Jan(?:uar)?|Feb(?:ruar)?|Mär(?:z)?|Apr(?:il)?|Mai|Jun(?:i)?|Jul(?:i)?|Aug(?:ust)?|Sep(?:tember)?|Okt(?:ober)?|Nov(?:ember)?|Dez(?:ember)?)\s\d{4}([\s]*$|.*(:|Im Namen))',
                r'Im Namen des']
        },
        Language.FR: {
            Section.FACTS: [r'Faits\s?:', r'en fait et en droit', r'(?:V|v)u\s?:', r'A.-'],
            Section.CONSIDERATIONS: [r'Considérant en (?:fait et en )?droit\s?:', r'(?:C|c)onsidérant(s?)\s?:',
                                     r'considère'],
            Section.RULINGS: [r'prononce\s?:', r'Par ces? motifs?\s?', r'ordonne\s?:'],
            Section.FOOTER: [
                r'\w*,\s(le\s?)?((\d?\d)|\d\s?(er|re|e)|premier|première|deuxième|troisième)\s?(?:janv|févr|mars|avr|mai|juin|juill|août|sept|oct|nov|déc).{0,10}\d?\d?\d\d\s?(.{0,5}[A-Z]{3}|(?!.{2})|[\.])',
                r'Au nom de la Cour'
            ]
        },
        Language.IT: {
            Section.FACTS: [r'(F|f)att(i|o)\s?:'],
            Section.CONSIDERATIONS: [r'(C|c)onsiderando', r'(D|d)iritto\s?:', r'Visto:', r'Considerato'],
            Section.RULINGS: [r'(P|p)er questi motivi'],
            Section.FOOTER: [
                r'\w*,\s(il\s?)?((\d?\d)|\d\s?(°))\s?(?:gen(?:naio)?|feb(?:braio)?|mar(?:zo)?|apr(?:ile)?|mag(?:gio)|giu(?:gno)?|lug(?:lio)?|ago(?:sto)?|set(?:tembre)?|ott(?:obre)?|nov(?:embre)?|dic(?:embre)?)\s?\d?\d?\d\d\s?([A-Za-z\/]{0,7}):?\s*$'
            ]
        }
    }

    valid_namespace(namespace, all_section_markers)

    section_markers = prepare_section_markers(all_section_markers, namespace)

    divs = decision.find_all("div", class_="content")
    # we expect maximally two divs with class content
    assert len(divs) <= 2

    paragraphs = get_paragraphs(decision)
    return associate_sections(paragraphs, section_markers, namespace)


def get_paragraphs(divs):
    # """
    # Get Paragraphs in the decision
    # :param divs:
    # :return:
    # """  
    paragraphs = []
    heading, paragraph = None, None
    for div in divs:
        for element in div:
            if isinstance(element, bs4.element.Tag):
                text = str(element.string)
                # This is a hack to also get tags which contain other tags such as links to BGEs
                if text.strip() == 'None':
                    text = element.get_text()
                # get numerated titles such as 1. or A.
                if "." in text and len(text) < 5:
                    heading = text  # set heading for the next paragraph
                else:
                    if heading is not None:  # if we have a heading
                        paragraph = heading + " " + text  # add heading to text of the next paragraph
                    else:
                        paragraph = text
                    heading = None  # reset heading
                paragraph = clean_text(paragraph)
                if paragraph not in ['', ' ', None]:  # discard empty paragraphs
                    paragraphs.append(paragraph)
        return paragraphs


def valid_namespace(namespace: dict, all_section_markers):
    if namespace['language'] not in all_section_markers:
        message = f"This function is only implemented for the languages {list(all_section_markers.keys())} so far."
        raise ValueError(message)


def prepare_section_markers(all_section_markers, namespace: dict) -> Dict[Section, str]:
    section_markers = all_section_markers[namespace['language']]
    section_markers = dict(
        map(lambda kv: (kv[0], '|'.join(kv[1])), section_markers.items()))
    for section, regexes in section_markers.items():
        section_markers[section] = unicodedata.normalize('NFC', regexes)
    return section_markers


def associate_sections(paragraphs: List[str], section_markers, namespace: dict):
    paragraphs_by_section = {section: [] for section in Section}
    current_section = Section.HEADER
    for paragraph in paragraphs:
        # update the current section if it changed
        current_section = update_section(current_section, paragraph, section_markers)

        # add paragraph to the list of paragraphs
        paragraphs_by_section[current_section].append(paragraph)
    if current_section != Section.FOOTER:
        # count how many times the footer wasn't reached
        global x
        x += 1
        print(x)
        # change the message depending on whether there's a url
        if namespace['html_url']:
            message = f"({namespace['id']}): We got stuck at section {current_section}. Please check! " \
                      f"Here you have the url to the decision: {namespace['html_url']}"
        elif 'pdf_url' in namespace and namespace['pdf_url']:
            message = f"({namespace['id']}): We got stuck at section {current_section}. Please check! " \
                      f"Here is the url to the decision: {namespace['pdf_url']}"
        else:
            message = f"({namespace['id']}): We got stuck at section {current_section}. Please check! " \
                      f"Here is the date of the decision: {namespace['date']}"
        raise ValueError(message)
    return paragraphs_by_section


def update_section(current_section: Section, paragraph: str, section_markers) -> Section:
    if current_section == Section.FOOTER:
        return current_section  # we made it to the end, hooray!
    sections = list(Section)
    next_section_index = sections.index(current_section) + 1
    # consider all following sections
    next_sections = sections[next_section_index:]
    for next_section in next_sections:
        marker = section_markers[next_section]
        paragraph = unicodedata.normalize('NFC', paragraph)  # if we don't do this, we get weird matching behaviour
        if re.search(marker, paragraph):
            return next_section  # change to the next section
    return current_section  # stay at the old section


# This needs special care
# def CH_BGE(decision: Any, namespace: dict) -> Optional[dict]:
#    return CH_BGer(decision, namespace)


def ZG_Verwaltungsgericht(decision: Union[bs4.BeautifulSoup, str], namespace: dict) -> Optional[
    Dict[Section, List[str]]]:
    """
    :param decision:    the decision parsed by bs4 or the string extracted of the pdf
    :param namespace:   the namespace containing some metadata of the court decision
    :return:            the sections dict (keys: section, values: list of paragraphs)
    """
    # As soon as one of the strings in the list (regexes) is encountered we switch to the corresponding section (key)
    all_section_markers = {
        Language.DE: {
            # "header" has no markers!
            Section.FACTS: [r'wird Folgendes festgestellt:', r'wird nach Einsicht in', r'^A\.\s'],
            Section.CONSIDERATIONS: [r'(Der|Die|Das) \w+ erwägt:', r'und in Erwägung, dass'],
            Section.RULINGS: [r'Demnach erkennt', r'Folgendes verfügt', r'(Der|Die|Das) \w+ verfügt:',
                              r'Demnach wird verfügt:'],
            Section.FOOTER: [
                r'^[\-\s\w\(]*,( den| vom)?\s\d?\d\.?\s?(?:Jan(?:uar)?|Feb(?:ruar)?|Mär(?:z)?|Apr(?:il)?|Mai|Jun(?:i)?|Jul(?:i)?|Aug(?:ust)?|Sep(?:tember)?|Okt(?:ober)?|Nov(?:ember)?|Dez(?:ember)?)\s\d{4}']
        }
    }

    if namespace['language'] not in all_section_markers:
        message = f"This function is only implemented for the languages {list(all_section_markers.keys())} so far."
        raise ValueError(message)

    section_markers = all_section_markers[namespace['language']]

    # combine multiple regex into one for each section due to performance reasons
    section_markers = dict(map(lambda kv: (kv[0], '|'.join(kv[1])), section_markers.items()))

    # normalize strings to avoid problems with umlauts
    for section, regexes in section_markers.items():
        section_markers[section] = unicodedata.normalize('NFC', regexes)
        # section_markers[key] = clean_text(regexes) # maybe this would solve some problems because of more cleaning

    def get_paragraphs(soup):
        """
        Get Paragraphs in the decision
        :param soup: the string extracted of the pdf
        :return: a list of paragraphs
        """
        paragraphs = []
        # remove spaces between two line breaks
        soup = re.sub('\\n +\\n', '\\n\\n', soup)
        # split the lines when there are two line breaks
        lines = soup.split('\n\n')
        for element in lines:
            element = element.replace('  ', ' ')
            paragraph = clean_text(element)
            if paragraph not in ['', ' ', None]:  # discard empty paragraphs
                paragraphs.append(paragraph)
        return paragraphs

    paragraphs = get_paragraphs(decision)
    return associate_sections(paragraphs, section_markers, namespace)


def ZH_Baurekurs(decision: Union[bs4.BeautifulSoup, str], namespace: dict) -> Optional[Dict[Section, List[str]]]:
    """
    :param decision:    the decision parsed by bs4 or the string extracted of the pdf
    :param namespace:   the namespace containing some metadata of the court decision
    :return:            the sections dict (keys: section, values: list of paragraphs)
    """
    # As soon as one of the strings in the list (regexes) is encountered we switch to the corresponding section (key)
    all_section_markers = {
        Language.DE: {
            # "header" has no markers!
            Section.FACTS: [r'hat sich ergeben', r'Gegenstand des Rekursverfahrens'],
            Section.CONSIDERATIONS: [r'Es kommt in Betracht', r'Aus den Erwägungen'],
            Section.RULINGS: [r'Zusammengefasst (ist|sind)', r'Zusammenfassend ist festzuhalten',
                              r'Zusammengefasst ergibt sich', r'Der Rekurs ist nach', r'Gesamthaft ist der Rekurs'],
            # this court has few if any footers
            Section.FOOTER: [
                r'^[\-\s\w\(]*,( den| vom)?\s\d?\d\.?\s?(?:Jan(?:uar)?|Feb(?:ruar)?|Mär(?:z)?|Apr(?:il)?|Mai|Jun(?:i)?|Jul(?:i)?|Aug(?:ust)?|Sep(?:tember)?|Okt(?:ober)?|Nov(?:ember)?|Dez(?:ember)?)\s\d{4}']
        },
    }

    if namespace['language'] not in all_section_markers:
        message = f"This function is only implemented for the languages {list(all_section_markers.keys())} so far."
        raise ValueError(message)

    section_markers = all_section_markers[namespace['language']]

    # combine multiple regex into one for each section due to performance reasons
    section_markers = dict(map(lambda kv: (kv[0], '|'.join(kv[1])), section_markers.items()))

    # normalize strings to avoid problems with umlauts
    for section, regexes in section_markers.items():
        section_markers[section] = unicodedata.normalize('NFC', regexes)
        # section_markers[key] = clean_text(regexes) # maybe this would solve some problems because of more cleaning

    def get_paragraphs(soup):
        """
        Get Paragraphs in the decision
        :param soup:
        :param soup: the string extracted of the pdf
        :return: a list of paragraphs
        """
        paragraphs = []
        # remove spaces between two line breaks
        soup = re.sub('\\n +\\n', '\\n\\n', soup)
        # split the lines when there are two line breaks
        lines = soup.split('\n\n')
        for element in lines:
            element = element.replace('  ', ' ')
            paragraph = clean_text(element)
            if paragraph not in ['', ' ', None]:  # discard empty paragraphs
                paragraphs.append(paragraph)
        return paragraphs

    paragraphs = get_paragraphs(decision)
    return associate_sections(paragraphs, section_markers, namespace)


def ZH_Obergericht(decision: Union[bs4.BeautifulSoup, str], namespace: dict) -> Optional[Dict[Section, List[str]]]:
    """
    :param decision:    the decision parsed by bs4 or the string extracted of the pdf
    :param namespace:   the namespace containing some metadata of the court decision
    :return:            the sections dict (keys: section, values: list of paragraphs)
    """
    # As soon as one of the strings in the list (regexes) is encountered we switch to the corresponding section (key)
    all_section_markers = {
        Language.DE: {
            # "header" has no markers!
            Section.FACTS: [r'betreffend'],
            Section.CONSIDERATIONS: [r'Erwägungen:', r'Das Gericht erwägt'],
            Section.RULINGS: [r'Es wird (erkannt|beschlossen|verfügt):', r'Das Gericht beschliesst:',
                              r'(Sodann|Demnach) beschliesst das Gericht:'],
            Section.FOOTER: [
                r'^[\-\s\w\(]*,( den| vom)?\s\d?\d\.?\s?(?:Jan(?:uar)?|Feb(?:ruar)?|Mär(?:z)?|Apr(?:il)?|Mai|Jun(?:i)?|Jul(?:i)?|Aug(?:ust)?|Sep(?:tember)?|Okt(?:ober)?|Nov(?:ember)?|Dez(?:ember)?)\s\d{4}([\s]*$|.*(:|Im Namen))',
                r'Obergericht des Kantons Zürich', r'OBERGERICHT DES KANTONS ZÜRICH']
        }
    }

    if namespace['language'] not in all_section_markers:
        message = f"This function is only implemented for the languages {list(all_section_markers.keys())} so far."
        raise ValueError(message)

    section_markers = all_section_markers[namespace['language']]
    # combine multiple regex into one for each section due to performance reasons
    section_markers = dict(map(lambda kv: (kv[0], '|'.join(kv[1])), section_markers.items()))

    # normalize strings to avoid problems with umlauts
    for section, regexes in section_markers.items():
        section_markers[section] = unicodedata.normalize('NFC', regexes)
        # section_markers[key] = clean_text(regexes) # maybe this would solve some problems because of more cleaning

    def get_paragraphs(soup):
        """
        Get Paragraphs in the decision
        :param soup: the string extracted of the pdf
        :return: a list of paragraphs
        """
        paragraphs = []
        # remove spaces between two line breaks
        soup = re.sub('\\n +\\n', '\\n\\n', soup)
        # split the lines when there are two line breaks
        lines = soup.split('\n\n')
        for element in lines:
            element = element.replace('  ', ' ')
            paragraph = clean_text(element)
            if paragraph not in ['', ' ', None]:  # discard empty paragraphs
                paragraphs.append(paragraph)
        return paragraphs

    paragraphs = get_paragraphs(decision)
    return associate_sections(paragraphs, section_markers, namespace)


def ZH_Sozialversicherungsgericht(decision: Union[bs4.BeautifulSoup, str], namespace: dict) -> Optional[
    Dict[Section, List[str]]]:
    """
    :param decision:    the decision parsed by bs4 or the string extracted of the pdf
    :param namespace:   the namespace containing some metadata of the court decision
    :return:            the sections dict (keys: section, values: list of paragraphs)
    """
    # As soon as one of the strings in the list (regexes) is encountered we switch to the corresponding section (key)
    all_section_markers = {
        Language.DE: {
            # "header" has no markers!
            Section.FACTS: [r'Sachverhalt:'],
            Section.CONSIDERATIONS: [r'in Erwägung, dass', r'zieht in Erwägung:', r'Erwägungen:'],
            Section.RULINGS: [r'Das Gericht (erkennt|beschliesst):',
                              r'(Der|Die) Einzelrichter(in)? (erkennt|beschliesst):', r'erkennt das Gericht:',
                              r'und erkennt sodann:'],
            # this court doesn't always have a footer
            Section.FOOTER: [r'Sozialversicherungsgericht des Kantons Zürich']
        }
    }

    if namespace['language'] not in all_section_markers:
        message = f"This function is only implemented for the languages {list(all_section_markers.keys())} so far."
        raise ValueError(message)

    section_markers = all_section_markers[namespace['language']]

    # combine multiple regex into one for each section due to performance reasons
    section_markers = dict(map(lambda kv: (kv[0], '|'.join(kv[1])), section_markers.items()))

    # normalize strings to avoid problems with umlauts
    for section, regexes in section_markers.items():
        section_markers[section] = unicodedata.normalize('NFC', regexes)
        # section_markers[key] = clean_text(regexes) # maybe this would solve some problems because of more cleaning

    def get_paragraphs(soup):
        """
        Get Paragraphs in the decision
        :param soup: the decision parsed by bs4
        :return: a list of paragraphs
        """
        # this should be the div closest to the content
        divs = soup.find("div", id="view:_id1:inputRichText1")
        # sometimes the content is not directly below but nested in other divs
        if len(divs) < 2:
            divs = divs.find('div')

        paragraphs = []
        heading, paragraph = None, None
        for element in divs:
            if isinstance(element, bs4.element.Tag):
                text = str(element.string)
                # This is a hack to also get tags which contain other tags such as links to BGEs
                if text.strip() == 'None':
                    text = element.get_text()
                # get numerated titles such as 1. or A.
                if "." in text and len(text) < 5:
                    heading = text  # set heading for the next paragraph
                else:
                    if heading is not None:  # if we have a heading
                        paragraph = heading + " " + text  # add heading to text of the next paragraph
                    else:
                        paragraph = text
                    heading = None  # reset heading
                if paragraph not in ['', ' ', None]:  # only clean non-empty paragraphs
                    paragraph = clean_text(paragraph)
                if paragraph not in ['', ' ', None]:  # discard empty paragraphs
                    paragraphs.append(paragraph)
        return paragraphs

    paragraphs = get_paragraphs(decision)
    return associate_sections(paragraphs, section_markers, namespace)


def ZH_Steuerrekurs(decision: Union[bs4.BeautifulSoup, str], namespace: dict) -> Optional[Dict[Section, List[str]]]:
    """
    :param decision:    the decision parsed by bs4 or the string extracted of the pdf
    :param namespace:   the namespace containing some metadata of the court decision
    :return:            the sections dict (keys: section, values: list of paragraphs)
    """
    # As soon as one of the strings in the list (regexes) is encountered we switch to the corresponding section (key)
    all_section_markers = {
        Language.DE: {
            # "header" has no markers!
            Section.FACTS: [r'hat sich ergeben:'],
            Section.CONSIDERATIONS: [r'zieht in Erwägung:', r'sowie in der Erwägung'],
            Section.RULINGS: [r'Demgemäss (erkennt|beschliesst)', r'beschliesst die Rekurskommission'],
            # often there is no footer
            Section.FOOTER: [
                r'^[\-\s\w\(]*,( den| vom)?\s\d?\d\.?\s?(?:Jan(?:uar)?|Feb(?:ruar)?|Mär(?:z)?|Apr(?:il)?|Mai|Jun(?:i)?|Jul(?:i)?|Aug(?:ust)?|Sep(?:tember)?|Okt(?:ober)?|Nov(?:ember)?|Dez(?:ember)?)\s\d{4}([\s]*$|.*(:|Im Namen))',
                r'Im Namen des']
        }
    }

    if namespace['language'] not in all_section_markers:
        message = f"This function is only implemented for the languages {list(all_section_markers.keys())} so far."
        raise ValueError(message)

    section_markers = all_section_markers[namespace['language']]
    # combine multiple regex into one for each section due to performance reasons
    section_markers = dict(map(lambda kv: (kv[0], '|'.join(kv[1])), section_markers.items()))

    # normalize strings to avoid problems with umlauts
    for section, regexes in section_markers.items():
        section_markers[section] = unicodedata.normalize('NFC', regexes)
        # section_markers[key] = clean_text(regexes) # maybe this would solve some problems because of more cleaning

    def get_paragraphs(soup):
        """
        Get Paragraphs in the decision
        :param soup: the string extracted of the pdf
        :return: a list of paragraphs
        """

        paragraphs = []
        # remove spaces between two line breaks
        soup = re.sub('\\n +\\n', '\\n\\n', soup)
        # split the lines when there are two line breaks
        lines = soup.split('\n\n')
        for element in lines:
            element = element.replace('  ', ' ')
            paragraph = clean_text(element)
            if paragraph not in ['', ' ', None]:  # discard empty paragraphs
                paragraphs.append(paragraph)
        return paragraphs

    paragraphs = get_paragraphs(decision)
    return associate_sections(paragraphs, section_markers, namespace)


def ZH_Verwaltungsgericht(decision: Union[bs4.BeautifulSoup, str], namespace: dict) -> Optional[
    Dict[Section, List[str]]]:
    """
    :param decision:    the decision parsed by bs4 or the string extracted of the pdf
    :param namespace:   the namespace containing some metadata of the court decision
    :return:            the sections dict (keys: section, values: list of paragraphs)
    """
    # As soon as one of the strings in the list (regexes) is encountered we switch to the corresponding section (key)
    all_section_markers = {
        Language.DE: {
            # "header" has no markers!
            Section.FACTS: [r'hat sich ergeben:', r'^\s*I\.\s+A\.\s*', r'^\s*I\.\s+$'],
            Section.CONSIDERATIONS: [r'erwägt:', r'zieht in Erwägung:'],
            Section.RULINGS: [r'Demgemäss (erkennt|beschliesst|entscheidet)'],
            # this court generally has no footer
            Section.FOOTER: [
                r'^[\-\s\w\(]*,( den| vom)?\s\d?\d\.?\s?(?:Jan(?:uar)?|Feb(?:ruar)?|Mär(?:z)?|Apr(?:il)?|Mai|Jun(?:i)?|Jul(?:i)?|Aug(?:ust)?|Sep(?:tember)?|Okt(?:ober)?|Nov(?:ember)?|Dez(?:ember)?)\s\d{4}([\s]*$|.*(:|Im Namen))',
                r'Im Namen des']
        }
    }

    if namespace['language'] not in all_section_markers:
        message = f"This function is only implemented for the languages {list(all_section_markers.keys())} so far."
        raise ValueError(message)

    section_markers = all_section_markers[namespace['language']]

    # combine multiple regex into one for each section due to performance reasons
    section_markers = dict(map(lambda kv: (kv[0], '|'.join(kv[1])), section_markers.items()))

    # normalize strings to avoid problems with umlauts
    for section, regexes in section_markers.items():
        section_markers[section] = unicodedata.normalize('NFC', regexes)
        # section_markers[key] = clean_text(regexes) # maybe this would solve some problems because of more cleaning

    def get_paragraphs(soup):
        """
        Get Paragraphs in the decision
        :param soup: the decision parsed by bs4 
        :return: a list of paragraphs
        """
        # sometimes the div with the content is called WordSection1
        divs = soup.find_all("div", class_="WordSection1")
        # sometimes the div with the content is called Section1
        if len(divs) == 0:
            divs = soup.find_all("div", class_="Section1")
        # we expect maximally two divs with class WordSection1
        assert (len(divs) <= 2), "Found more than two divs with class WordSection1"
        assert (len(divs) > 0), "Found no div, " + str(namespace['html_url'])

        paragraphs = []
        heading, paragraph = None, None
        for element in divs[0]:
            if isinstance(element, bs4.element.Tag):
                text = str(element.string)
                # This is a hack to also get tags which contain other tags such as links to BGEs
                if text.strip() == 'None':
                    text = element.get_text()
                # get numerated titles such as 1. or A.
                if "." in text and len(text) < 5:
                    heading = text  # set heading for the next paragraph
                else:
                    if heading is not None:  # if we have a heading
                        paragraph = heading + " " + text  # add heading to text of the next paragraph
                    else:
                        paragraph = text
                    heading = None  # reset heading
                if paragraph not in ['', ' ', None]:  # only clean non-empty paragraphs
                    paragraph = clean_text(paragraph)
                if paragraph not in ['', ' ', None]:  # discard empty paragraphs
                    paragraphs.append(paragraph)
        return paragraphs

    paragraphs = get_paragraphs(decision)
    return associate_sections(paragraphs, section_markers, namespace)
