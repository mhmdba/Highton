# -*- coding: utf-8 -*-
import datetime

import requests
from lxml import objectify, etree
from requests.auth import HTTPBasicAuth

from custom_exceptions import (HighriseGetException, ParseTimeException,
                               FieldException, XMLRequestException)
from classes.person import Person
from classes.category import DealCategory, TaskCategory
from classes.company import Company
from classes.case import Case
from classes.deal import Deal
from classes.task import Task
from classes.note import Note
from classes.email import Email
from classes.deletions import Deletion
from classes.tools import to_datetime


class Highton(object):
    """
        Highton-API is just a really simple Python library which helps you to
        get information about your Highrise data
    """

    def __init__(self, api_key, user):
        self.user = user
        self.api_key = api_key
        self.api_key_password = 'X'

    def _get_request(self, endpoint, params={}):
        url = 'https://{}.highrisehq.com/{}.xml'.format(self.user, endpoint)
        request = requests.get(
            url,
            auth=HTTPBasicAuth(self.api_key, self.api_key_password),
            headers={'User-Agent': 'Highton-API: (bykof@me.com)'},
            params=params,
        )

        if 'text/html' in request.headers['content-type']:
            raise XMLRequestException(url)

        return request

    def set_account(self, params={}):
        """
        Set the account on the Highton instance. There really isn't a reason
        not to since there should be only one account here.
        """
        account = objectify.fromstring(
            self._get_request('account', params).content
        )
        self.account = {}
        self.account['highrise_id'] = account['id'].pyval
        self.account['created_at'] = to_datetime(account['created-at'].pyval)
        self.account['updated_at'] = to_datetime(account['updated-at'].pyval)
        for attr in [
            'name',
            'subdomain',
            'plan',
            'color_theme',
            'ssl_enabled',
            'people-count',
            'storage'
        ]:
            self.account[attr.replace('-', '_')] = account[attr].pyval

    def _get_single_data(self, endpoint, params={}):
        data = []
        try:
            data = objectify.fromstring(
                self._get_request(endpoint, params).content
            )
        except TypeError:
            if not data:
                raise HighriseGetException(
                    endpoint,
                    'Parsing data from Highrise caused a failure'
                )
        return data

    def _get_data(self, endpoint, params={}):
        data = []
        try:
            data = objectify.fromstring(
                self._get_request(endpoint, params).content
            ).getchildren()
        except TypeError:
            if not data:
                raise HighriseGetException(
                    endpoint,
                    'Parsing data from Highrise caused a failure'
                )
        return data

    def _get_paged_data(self, endpoint, params={}):
        data = []
        try:
            page = 500
            counter = 0
            while True:
                params.update({'n': page * counter})
                objects = objectify.fromstring(
                    self._get_request(endpoint, params).content
                ).getchildren()
                if objects:
                    data += objects
                else:
                    break
                counter += 1
        except TypeError:
            if not data:
                raise HighriseGetException(
                    endpoint,
                    'Parsing people from Highrise caused a failure'
                )
        return data

    def _get_object_data(self, data, highrise_class):
        """
        Return a formatted highrise_class list.
        """
        data_list = []
        for d in data:
            temp = highrise_class()
            temp.save_data(d)
            data_list.append(temp)
        return data_list

    def _put_request(self, endpoint, data=None, params={}):
        url = 'https://{}.highrisehq.com/{}.xml'.format(
            self.user, endpoint, params)
        request = requests.put(
            url,
            auth=HTTPBasicAuth(self.api_key, self.api_key_password),
            headers={
                'User-Agent': 'Highton-API: (bykof@me.com)',
                'content-type': 'application/xml'
            },
            params=params,
            data=data
        )

        if 'text/html' in request.headers['content-type']:
            raise XMLRequestException(url)

        return request

    def _delete_request(self, endpoint, params={}):
        url = 'https://{}.highrisehq.com/{}.xml'.format(
            self.user, endpoint, params)
        request = requests.delete(
            url,
            auth=HTTPBasicAuth(self.api_key, self.api_key_password),
            headers={
                'User-Agent': 'Highton-API: (bykof@me.com)',
            },
            params=params,
        )

        if 'text/html' in request.headers['content-type']:
            raise XMLRequestException(url)

        return request

    def get_person(self, subject_id):
        """
        Gives you a chosen person as an object.
        :param subject_id: the highrise_id of the deal
        :return: person object
        """
        return self._get_object_data(self._get_single_data('people/{}'.format(
            subject_id)), Person)[0]

    def get_people(self):
        """
        Just run this Method and you get a Person object with all objects and
        attributes inside it. Get Lucky
        :return: returns all people (of course it iterates over all pages, so
            you dont get only the first 500)
        """
        return self._get_object_data(self._get_paged_data('people'), Person)

    def get_people_since(self, since):
        """
        Gives you all people since the set parameter
        :param since: string with %Y%m%d%H%M%S - Format
        :return: return all people since the given parameter
        """
        try:
            datetime.datetime.strptime(since, '%Y%m%d%H%M%S')
        except ValueError:
            raise ParseTimeException
        return self._get_object_data(self._get_paged_data(
            'people', params={'since': since}), Person)

    def _get_categories(self, category_type):
        return self._get_data(category_type + '_categories')

    def get_task_categories(self):
        """
        Get all Task-Categories
        :return: all Task-Categories
        """
        return self._get_object_data(
            self._get_categories('task'), TaskCategory)

    def get_deal_categories(self):
        """
        Get all Deal-Categories
        :return: all Deal-Categories
        """
        return self._get_object_data(
            self._get_categories('deal'), DealCategory)

    def get_company(self, subject_id):
        """
        Gives you a chosen company as an object.
        :param subject_id: the highrise_id of the deal
        :return: company object
        """
        return self._get_object_data(self._get_single_data(
            'companies/{}'.format(subject_id)), Company)[0]

    def get_companies(self):
        """
        Just run this Method and you get a Company object with all objects and
        attributes inside it. Get Lucky
        :return: returns all people (of course it iterates over all pages, so
            you dont get only the first 500)
        """
        return self._get_object_data(
            self._get_paged_data('companies'), Company)

    def get_companies_since(self, since):
        """
        Gives you all companies since the set parameter
        :param since: string with %Y%m%d%H%M%S - Format
        :return: return all companies since the given parameter
        """
        try:
            datetime.datetime.strptime(since, '%Y%m%d%H%M%S')
        except ValueError:
            raise ParseTimeException
        return self._get_object_data(self._get_paged_data(
            'companies', params={'since': since}), Company)

    def get_case(self, subject_id):
        """
        Gives you a chosen case as an object.
        :param subject_id: the highrise_id of the deal
        :return: case object
        """
        return self._get_object_data(self._get_single_data('kases/{}'.format(
            subject_id)), Case)[0]

    def get_cases(self):
        """
        Just run this Method and you get a Case object with all objects and
        attributes inside it. Get Lucky
        :return: returns all people (of course it iterates over all pages, so
            you dont get only the first 500)
        """
        return self._get_object_data(self._get_paged_data('kases'), Case)

    def get_cases_since(self, since):
        """
        Gives you all Cases since the set parameter
        :param since: string with %Y%m%d%H%M%S - Format
        :return: return all cases since the given parameter
        """
        try:
            datetime.datetime.strptime(since, '%Y%m%d%H%M%S')
        except ValueError:
            raise ParseTimeException(since)
        return self._get_object_data(self._get_paged_data(
            'kases', params={'since': since}), Case)

    def get_deal(self, subject_id):
        """
        Gives you a chosen deal as an object
        :param subject_id: the highrise_id of the deal
        :return: deal object
        """
        return self._get_object_data(self._get_single_data('deals/{}'.format(
            subject_id)), Deal)[0]

    def get_deals(self):
        """
        Gives you all Deals, but handle them wisely!
        :return: returns you all the Deals you have
        """
        return self._get_object_data(self._get_paged_data('deals'), Deal)

    def get_deals_since(self, since):
        """
        Gives you all deals since the parameter since
        :param since: Have to be String in format YYYYMMDDHHMMSS
        :return: returns you all Deals which were updated since the parameter
        """
        try:
            datetime.datetime.strptime(since, '%Y%m%d%H%M%S')
        except ValueError:
            raise ParseTimeException
        return self._get_object_data(self._get_paged_data(
            'deals', params={'since': since}), Deal)

    def get_deals_by_status(self, status):
        fields = ['won', 'lost', 'pending']
        if status not in fields:
            raise FieldException(fields)
        return self._get_object_data(self._get_paged_data(
            'deals', params={'status': status}), Deal)

    def get_task(self, subject_id):
        """
        Gives you a chosen task as an object.
        :param subject_id: the highrise_id of the deal
        :return: task object
        """
        return self._get_object_data(self._get_single_data('tasks/{}'.format(
            subject_id)), Task)[0]

    def _get_tasks(self, subject_id, highrise_type):
        return self._get_object_data(self._get_data('{}/{}/tasks'.format(
            highrise_type, subject_id)), Task)

    def get_tasks(self):
        return self._get_object_data(self._get_data('tasks/all'), Task)

    def get_person_tasks(self, subject_id):
        return self._get_tasks(subject_id, 'people')

    def get_company_tasks(self, subject_id):
        return self._get_tasks(subject_id, 'companies')

    def get_case_tasks(self, subject_id):
        return self._get_tasks(subject_id, 'kases')

    def get_deal_tasks(self, subject_id):
        return self._get_tasks(subject_id, 'deals')

    def _get_notes(self, subject_id, highrise_type):
        return self._get_object_data(self._get_data('{}/{}/notes'.format(
            highrise_type, subject_id)), Note)

    def get_person_notes(self, subject_id):
        return self._get_notes(subject_id, 'people')

    def get_company_notes(self, subject_id):
        return self._get_notes(subject_id, 'companies')

    def get_case_notes(self, subject_id):
        return self._get_notes(subject_id, 'kases')

    def get_deal_notes(self, subject_id):
        return self._get_notes(subject_id, 'deals')

    def _get_emails(self, subject_id, highrise_type):
        return self._get_object_data(self._get_data('{}/{}/emails'.format(
            highrise_type, subject_id)), Email)

    def get_person_emails(self, subject_id):
        return self._get_emails(subject_id, 'people')

    def get_company_emails(self, subject_id):
        return self._get_emails(subject_id, 'companies')

    def get_case_emails(self, subject_id):
        return self._get_emails(subject_id, 'kases')

    def get_deal_emails(self, subject_id):
        return self._get_emails(subject_id, 'deals')

    def get_deletions(self, params={}):
        # Get the xml data in an etree obj since we have lxml.
        # This object type is odd since the `type` attr is attached
        # to the xml at a parent level relative to the placement
        # of the rest of the data.
        _deletions = etree.fromstring(
            self._get_request('deletions', params).content)
        deletions = []
        for deletion in _deletions:
            data = {}
            data['type'] = deletion.attrib.values()[0]
            for sub in deletion:
                data[sub.tag] = sub.text
            temp = Deletion()
            temp.save_data(data)
            deletions.append(temp)
        return deletions

    def get_deletions_since(self, since):
        """
        Gives you all deletions since the set parameter
        :param since: string with %Y%m%d%H%M%S - Format
        :return: return all deletions since the given parameter
        """
        try:
            datetime.datetime.strptime(since, '%Y%m%d%H%M%S')
        except ValueError:
            raise ParseTimeException
        return self.get_deletions(params={'since': since})

    def put_case(self, highrise_id, data, params={}):
        return self._put_request('kases/{}'.format(highrise_id), data, params)

    def put_comment(self, highrise_id, data, params={}):
        return self._put_request(
            'comments/{}'.format(highrise_id), data, params)

    def put_company(self, highrise_id, data, params={}):
        return self._put_request(
            'companies/{}'.format(highrise_id), data, params)

    def put_custom_field(self, highrise_id, data, params={}):
        return self._put_request(
            'subject_field/{}'.format(highrise_id), data, params)

    def put_deal(self, highrise_id, data, params={}):
        return self._put_request('deals/{}'.format(highrise_id), data, params)

    def put_email(self, highrise_id, data, params={}):
        return self._put_request('emails/{}'.format(highrise_id), data, params)

    def put_group(self, highrise_id, data, params={}):
        return self._put_request('groups/{}'.format(highrise_id), data, params)

    def put_note(self, highrise_id, data, params={}):
        return self._put_request('notes/{}'.format(highrise_id), data, params)

    def put_person(self, highrise_id, data, params={}):
        return self._put_request('people/{}'.format(highrise_id), data, params)

    def put_task(self, highrise_id, data, params={}):
        return self._put_request('tasks/{}'.format(highrise_id), data, params)

    def delete_case(self, highrise_id, params={}):
        return self._delete_request('kases/{}'.format(highrise_id), params)

    def delete_category(self, model_type, highrise_id, params={}):
        return self._delete_request(
            '{}_categories/{}'.format(model_type, highrise_id), params)

    def delete_comment(self, highrise_id, params={}):
        return self._delete_request('comments/{}'.format(highrise_id), params)

    def delete_company(self, highrise_id, params={}):
        return self._delete_request(
            'companies/{}'.format(highrise_id), params)

    def delete_custom_field(self, highrise_id, params={}):
        return self._delete_request(
            'subject_field/{}'.format(highrise_id), params)

    def delete_deal(self, highrise_id, params={}):
        return self._delete_request('deals/{}'.format(highrise_id), params)

    def delete_email(self, highrise_id, params={}):
        return self._delete_request('emails/{}'.format(highrise_id), params)

    def delete_group(self, highrise_id, params={}):
        return self._delete_request('groups/{}'.format(highrise_id), params)

    def delete_membership(self, highrise_id, params={}):
        return self._delete_request(
            'memberships/{}'.format(highrise_id), params)

    def delete_note(self, highrise_id, params={}):
        return self._delete_request('notes/{}'.format(highrise_id), params)

    def delete_person(self, highrise_id, params={}):
        return self._delete_request('people/{}'.format(highrise_id), params)

    def delete_tag(self, subject_type, subject_id, highrise_id, params={}):
        """
        A delete call for a tag requires a specific path.
        DELETE /#{subject_type}/#{subject_id}/tags/#{id}.xml
        """
        return self._delete_request('{}/{}/tags/{}'.format(
            subject_type, subject_id, highrise_id), params)

    def delete_task(self, highrise_id, params={}):
        return self._delete_request('tasks/{}'.format(highrise_id), params)
