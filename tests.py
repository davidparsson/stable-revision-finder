#!/usr/bin/python
#
# Run tests using Python 2.7 with the command
#  python tests.py
# after installing the dependencies
#  sudo easy_install unittest-xml-reporting
#  sudo easy_install mockito
#
import unittest
import xmlrunner
from mockito import mock, when, contains
from find_last_stable_revision import *
import find_last_stable_revision
import json
from datetime import datetime

class FakeDatetime():

    def __init__(self, datetime_mock):
        self.datetime_mock = datetime_mock

    def now(self):
        return self.datetime_mock.now()

    def fromtimestamp(self, timestamp):
        return datetime.fromtimestamp(timestamp)


class AcceptanceTest(unittest.TestCase):

    view_url = "http://jenkins/view"

    def setUp(self):
        self.urllib = mock()
        self.datetime_mock = mock()
        self.datetime_fake = FakeDatetime(self.datetime_mock)
        self.given_time_is(0)
        find_last_stable_revision.urllib = self.urllib
        find_last_stable_revision.datetime = self.datetime_fake
        self.number_of_jobs = 0
        self.response = {'jobs': []}

    def test_does_not_select_buildling_revision(self):
        self.given_job_with_builds(build(2), build(1))
        self.given_job_with_builds(build(2, building=True), build(1))
        self.assertEqual(1, find_last_stable_revision.find_revision(self.view_url)[0])

    def test_does_not_select_revision_after_buildling_revision(self):
        self.given_job_with_builds(build(3), build(1))
        self.given_job_with_builds(build(2, building=True), build(1))
        self.assertEqual(1, find_last_stable_revision.find_revision(self.view_url)[0])

    def test_does_not_select_unstable_revision(self):
        self.given_job_with_builds(build(2), build(1))
        self.given_job_with_builds(build(2, stable=False), build(1))
        self.assertEqual(1, find_last_stable_revision.find_revision(self.view_url)[0])

    def test_does_not_select_revision_after_unstable_build(self):
        self.given_job_with_builds(build(3), build(1))
        self.given_job_with_builds(build(2, stable=False), build(1))
        self.assertEqual(1, find_last_stable_revision.find_revision(self.view_url)[0])

    def test_selects_stable_revision_after_unstable_build(self):
        self.given_job_with_builds(build(2), build(1))
        self.given_job_with_builds(build(3), build(2, stable=False), build(1))
        self.assertEqual(3, find_last_stable_revision.find_revision(self.view_url)[0])

    def test_selects_highest_stable_revision(self):
        self.given_job_with_builds(build(3), build(1))
        self.given_job_with_builds(build(2), build(1))
        self.assertEqual(3, find_last_stable_revision.find_revision(self.view_url)[0])

    def test_selects_revision_even_if_not_built(self):
        self.given_job_with_builds(build(1))
        self.given_job_with_builds()
        self.assertEqual(1, find_last_stable_revision.find_revision(self.view_url)[0])

    def test_does_not_selects_revision_when_none_built(self):
        self.given_job_with_builds()
        self.given_job_with_builds()
        self.assertEqual(-1, find_last_stable_revision.find_revision(self.view_url)[0])

    def test_selects_highest_revision_when_multiple_changes(self):
        self.given_job_with_builds(build([3, 2, 1]))
        self.assertEqual(3, find_last_stable_revision.find_revision(self.view_url)[0])

    def test_selects_highest_revision_when_not_sorted(self):
        self.given_job_with_builds(build(2), build([1, 7, 3]), build(4))
        self.given_job_with_builds(build(6), build(2), build(5))
        self.assertEqual(7, find_last_stable_revision.find_revision(self.view_url)[0])

    def test_gets_timestamp_for_latest_revision(self):
        self.given_time_is(5)
        self.given_job_with_builds(build(3, timestamp=3), build(2, timestamp=2))
        self.assertEqual(2, find_last_stable_revision.find_revision(self.view_url)[1].seconds)

    def test_gets_timestamp_for_latest_stable_revision(self):
        self.given_time_is(5)
        self.given_job_with_builds(build(3, timestamp=3, stable=False), build(2, timestamp=2))
        self.assertEqual(3, find_last_stable_revision.find_revision(self.view_url)[1].seconds)

    def given_time_is(self, timestamp):
        when(self.datetime_mock).now().thenReturn(datetime.fromtimestamp(timestamp))

    def given_job_with_builds(self, *builds):
        job_number = len(self.response['jobs'])
        current_job = job(job_number)
        current_job['builds'] = builds

        self.response['jobs'].append(current_job)

        self.rebuild_response()

    def rebuild_response(self):
        response = str(self.response)
        self.given_response_for_url("?tree=jobs", response)

    def given_response_for_url(self, url, response):
        open_url = mock()
        when(self.urllib).urlopen(contains(url)).thenReturn(open_url)
        when(open_url).read().thenReturn(response)

class TestRevisionStatuses(unittest.TestCase):

    def setUp(self):
        self.revision_statuses = RevisionStatuses()

    def test_not_stable_when_no_added_revisions(self):
        self.assertIsNone(self.revision_statuses.is_revision_stable(1))

    def test_added_stable_revision_is_stable(self):
        self.revision_statuses.add_stable_revision(1)
        self.assertTrue(self.revision_statuses.is_revision_stable(1))

    def test_revision_after_added_stable_revision_is_stable(self):
        self.revision_statuses.add_stable_revision(1)
        self.assertTrue(self.revision_statuses.is_revision_stable(2))

    def test_revision_before_added_stable_revision_not_stable(self):
        self.revision_statuses.add_stable_revision(2)
        self.assertIsNone(self.revision_statuses.is_revision_stable(1))

    def test_added_unstable_revision_is_not_stable(self):
        self.revision_statuses.add_stable_revision(1)
        self.revision_statuses.add_unstable_revision(2)
        self.assertFalse(self.revision_statuses.is_revision_stable(2))

    def test_revision_is_stable_if_stable_once(self):
        self.revision_statuses.add_unstable_revision(1)
        self.revision_statuses.add_stable_revision(1)
        self.revision_statuses.add_unstable_revision(1)
        self.assertTrue(self.revision_statuses.is_revision_stable(1))


def build(revisions=[], building=False, stable=True, timestamp=0):
    if stable:
        result = 'SUCCESS'
    else:
        result = 'FAILURE'

    if type(revisions) != list:
        revisions = [revisions]

    changes = [{'revision': revision, 'timestamp': timestamp * 1e3} for revision in revisions]
    return {'building': building, 'result': result, 'changeSet': {'items': changes}}


def job(number):
    return {'name': 'job%d' % number, 'url': 'http://jenkins/job/job%d/' % number}


if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
