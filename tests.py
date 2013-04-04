#!/usr/bin/python
#
# Run tests using Python 2.7 with the command
# python tests.py
#
import unittest
import xmlrunner
from mockito import mock, when, contains
from find_last_stable_revision import *
import find_last_stable_revision


class AcceptanceTest(unittest.TestCase):

    urllib = mock()
    view_url = "http://jenkins/view"

    def setUp(self):
        find_last_stable_revision.urllib = self.urllib
        self.number_of_jobs = 0

    def test_does_not_select_buildling_revision(self):
        self.given_job_with_builds(build(2), build(1))
        self.given_job_with_builds(build(2, building=True), build(1))
        self.assertEqual(1, find_last_stable_revision.find_revision(self.view_url))

    def test_does_not_select_revision_after_buildling_revision(self):
        self.given_job_with_builds(build(3), build(1))
        self.given_job_with_builds(build(2, building=True), build(1))
        self.assertEqual(1, find_last_stable_revision.find_revision(self.view_url))

    def test_does_not_select_unstable_revision(self):
        self.given_job_with_builds(build(2), build(1))
        self.given_job_with_builds(build(2, stable=False), build(1))
        self.assertEqual(1, find_last_stable_revision.find_revision(self.view_url))

    def test_does_not_select_revision_after_unstable_build(self):
        self.given_job_with_builds(build(3), build(1))
        self.given_job_with_builds(build(2, stable=False), build(1))
        self.assertEqual(1, find_last_stable_revision.find_revision(self.view_url))

    def test_selects_stable_revision_after_unstable_build(self):
        self.given_job_with_builds(build(2), build(1))
        self.given_job_with_builds(build(3), build(2, stable=False), build(1))
        self.assertEqual(3, find_last_stable_revision.find_revision(self.view_url))

    def test_selects_highest_stable_revision(self):
        self.given_job_with_builds(build(3), build(1))
        self.given_job_with_builds(build(2), build(1))
        self.assertEqual(3, find_last_stable_revision.find_revision(self.view_url))

    def test_selects_revision_even_if_not_built(self):
        self.given_job_with_builds(build(1))
        self.given_job_with_builds()
        self.assertEqual(1, find_last_stable_revision.find_revision(self.view_url))

    def test_does_not_selects_revision_when_none_built(self):
        self.given_job_with_builds()
        self.given_job_with_builds()
        self.assertEqual(-1, find_last_stable_revision.find_revision(self.view_url))

    def test_selects_highest_revision_when_multiple_changes(self):
        self.given_job_with_builds(build([3, 2, 1]))
        self.assertEqual(3, find_last_stable_revision.find_revision(self.view_url))

    def test_selects_highest_revision_when_not_sorted(self):
        self.given_job_with_builds(build(2), build([1, 7, 3]), build(4))
        self.given_job_with_builds(build(6), build(2), build(5))
        self.assertEqual(7, find_last_stable_revision.find_revision(self.view_url))

    def given_job_with_builds(self, *builds):
        url = "/job%d/api/python?tree=builds" % self.number_of_jobs
        response = self.create_builds_response(builds)

        self.number_of_jobs += 1

        self.given_response_for_url(url, response)
        self.given_number_of_jobs(self.number_of_jobs)

    def given_number_of_jobs(self, number_of_jobs):
        response = self.create_jobs_response(number_of_jobs)
        self.given_response_for_url("?tree=jobs", response)

    def given_response_for_url(self, url, response):
        open_url = mock()
        when(self.urllib).urlopen(contains(url)).thenReturn(open_url)
        when(open_url).read().thenReturn(response)

    def create_jobs_response(self, number_of_jobs):
        return '{"jobs":[%s]}' % ','.join([job(i) for i in range(number_of_jobs)])

    def create_builds_response(self, *builds):
        return '{"builds":[%s]}' % ','.join(builds)


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


def build(revisions=[], building=False, stable=True):
    if stable:
        result = 'SUCCESS'
    else:
        result = 'FAILURE'

    if type(revisions) != list:
        revisions = [revisions]

    return str({'building': building, 'result': result, 'changeSet': {'items': [{'revision': revision} for revision in revisions]}})


def job(number):
    return str({'name': 'job%d' % number, 'url': 'http://jenkins/job/job%d/' % number})


if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
