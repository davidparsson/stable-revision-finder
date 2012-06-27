#!/usr/bin/python
import unittest
from mockito import mock, when, contains, any
from find_last_stable_revision import *
import find_last_stable_revision


class AcceptanceTest(unittest.TestCase):

  urllib = mock()

  def setUp(self):
    find_last_stable_revision.urllib = self.urllib
    self. number_of_jobs = 0

  def test_does_not_select_buildling_revision(self):
    self.given_job_with_builds(build(2), build(1))
    self.given_job_with_builds(build(2, building=True), build(1))
    self.assertEqual(1, find_last_stable_revision.find_revision("url"))

  def test_does_not_select_unstable_revision(self):
    self.given_job_with_builds(build(2), build(1))
    self.given_job_with_builds(build(2, stable=False), build(1))
    self.assertEqual(1, find_last_stable_revision.find_revision("url"))

  def test_does_not_select_revision_after_unstable_build(self):
    self.given_job_with_builds(build(3), build(1))
    self.given_job_with_builds(build(2, stable=False), build(1))
    self.assertEqual(1, find_last_stable_revision.find_revision("url"))

  def test_selects_highest_stable_revision(self):
    self.given_job_with_builds(build(3), build(1))
    self.given_job_with_builds(build(2), build(1))
    self.assertEqual(3, find_last_stable_revision.find_revision("url"))

  def test_selects_revision_even_if_not_built(self):
    self.given_job_with_builds(build(1))
    self.given_job_with_builds()
    self.assertEqual(1, find_last_stable_revision.find_revision("url"))

  def test_selects_highest_revision_when_multiple_changes(self):
    self.given_job_with_builds(build([3, 2, 1]))
    self.assertEqual(3, find_last_stable_revision.find_revision("url"))

  def given_job_with_builds(self, *builds):
    url = "/job%d/api/python?tree=builds" % self.number_of_jobs
    response = '{"builds":[%s]}' % ','.join(builds)

    self.number_of_jobs += 1

    self.given_response_for_url(url, response)
    self.given_number_of_jobs(self.number_of_jobs)

  def given_number_of_jobs(self, number_of_jobs):
    response = '{"jobs":[%s]}' % ','.join([job(i) for i in range(number_of_jobs)])
    self.given_response_for_url("?tree=jobs", response)

  def given_response_for_url(self, url, response):
    open_url = mock()
    when(self.urllib).urlopen(contains(url)).thenReturn(open_url)
    when(open_url).read().thenReturn(response)


class TestSequenceFunctions(unittest.TestCase):

  def test_removes_duplicates(self):
    sequence = remove_duplicates([5, 2, 5, 5, 1])
    self.assertEqual([5, 2, 1], sequence)


class TestCleanAndSort(unittest.TestCase):

  def test_removes_duplicates(self):
    sequence = clean_and_sort([5, 5])
    self.assertEquals([5], sequence)

  def test_sorts_reversed(self):
    sequence = clean_and_sort([5, 1, 4])
    self.assertEquals([5, 4, 1], sequence)


class TestFindClosestPreviousRevision(unittest.TestCase):

  revisions = [2, 6, 3, 1]

  def test_finds_same_if_existing(self):
    revision = find_closest_previous_revision(3, self.revisions)
    self.assertEquals(3, revision)

  def test_finds_lesser_if_not_existing(self):
    revision = find_closest_previous_revision(4, self.revisions)
    self.assertEquals(3, revision)


class TestNoFailuresSinceLastStable(unittest.TestCase):

  def test_bad_revisions_between(self):
    self.assertTrue(failures_since_last_stable(10, 20, [15]))

  def test_bad_revisions_same_as_lower(self):
    self.assertTrue(failures_since_last_stable(10, 20, [10]))

  def test_bad_revisions_same_as_upper(self):
    self.assertTrue(failures_since_last_stable(10, 20, [20]))

  def test_no_bad_revisions(self):
    self.assertFalse(failures_since_last_stable(10, 20, []))

  def test_bad_revisions_before_and_after(self):
    self.assertFalse(failures_since_last_stable(10, 20, [5, 30]))


class TestGetHighestStableRevision(unittest.TestCase):

  def setUp(self):
    self.eligible_revisions = [1, 2, 3, 5, 7]
    self.bad_revisions = [2, 4, 6]
    self.good_revisions = {'job1': [1, 3, 4],
                           'job2': [3]}

  def test_minus_one_when_no_revision_found(self):
    self.assertEquals(-1, get_highest_stable_revision([], {}, []))

  def test_finds_revision(self):
    self.assertEquals(1, get_highest_stable_revision([1], {'job1': [1]}, []))

  def test_finds_highest_when_no_failures(self):
    self.assertEquals(2, get_highest_stable_revision([1, 2], {'job1': [1], 'job2': [1]}, []))

  def test_finds_highest_without_failures(self):
    self.assertEquals(1, get_highest_stable_revision([1, 2], {'job1': [1], 'job2': [1]}, [2]))

  def test_selects_lower_if_failures_between(self):
    self.assertEquals(2, get_highest_stable_revision([4, 2, 1], {'job1': [1], 'job2': [4, 2]}, [3]))


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
  unittest.main()