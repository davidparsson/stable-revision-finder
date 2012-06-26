#!/usr/bin/python
import unittest
from find_last_stable_revision import *

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

  def test_false_when_bad_revisions_between(self):
    self.assertFalse(no_failures_since_last_stable(10, 20, [15]))
  
  def test_false_when_bad_revisions_same_as_lower(self):
    self.assertFalse(no_failures_since_last_stable(10, 20, [10]))

  def test_false_when_bad_revisions_same_as_upper(self):
    self.assertFalse(no_failures_since_last_stable(10, 20, [20]))

  def test_true_when_no_bad_revisions(self):
    self.assertTrue(no_failures_since_last_stable(10, 20, []))

  def test_true_when_bad_revisions_before_and_after(self):
    self.assertTrue(no_failures_since_last_stable(10, 20, [5, 30]))

if __name__ == '__main__':
  unittest.main()