#!/usr/bin/python
import ast
import urllib
import sys

def parse(url, tree=None):
  if url[-1] != "/":
    url += "/"
  url = "%sapi/python" % url
  if tree:
    url += "?tree=%s" % tree
  return ast.literal_eval(urllib.urlopen(url).read())

def remove_duplicates(sequence):
  seen = set()
  seen_add = seen.add
  return [x for x in sequence if x not in seen and not seen_add(x)]

def clean_and_sort(sequence):
  sequence = remove_duplicates(sequence)
  sequence.sort()
  sequence.reverse()
  return sequence

def find_closest_previous_revision(revision, sequence):
  if not sequence:
    return -1
  return max(filter(lambda x: x <= revision, sequence))

def failures_since_last_stable(previous_stable_revision, eligible_revision, bad_revisions):
  for revision in range(previous_stable_revision, eligible_revision + 1):
    if revision in bad_revisions:
      return True
  return False

def is_stable_revision(eligible_revision, stable_build_revisions, bad_revisions):
  for job_name in stable_build_revisions:
    good_job_revisions = clean_and_sort(stable_build_revisions[job_name])
    previous_stable_revision = find_closest_previous_revision(eligible_revision, good_job_revisions)
    if failures_since_last_stable(previous_stable_revision, eligible_revision, bad_revisions):
      return False
  return True

def get_highest_stable_revision(eligible_revisions, stable_build_revisions, bad_revisions):
  eligible_revisions = clean_and_sort(eligible_revisions)
  bad_revisions = clean_and_sort(bad_revisions)

  for eligible_revision in eligible_revisions:
    if not eligible_revision in bad_revisions:
      if is_stable_revision(eligible_revision, stable_build_revisions, bad_revisions):
        return eligible_revision
  return -1

def find_revision(url, verbose=False):
  view_details = parse(url, "jobs[name,url]")

  stable_build_revisions = {}
  eligible_revisions = []
  bad_revisions = []
  for job in view_details['jobs']:
    if verbose:
      print "Querying %s..." % job['name']
    result = parse(job['url'], "builds[building,result,changeSet[items[revision]]]")

    current_stable_build_revisions = []
    stable_build_revisions[job['name']] = current_stable_build_revisions

    for build in result['builds']:
      if not build['building'] and build['result'] == 'SUCCESS':
        for item in build['changeSet']['items']:
          current_stable_build_revisions.append(item['revision'])
          eligible_revisions.append(item['revision'])
      else:
        for item in build['changeSet']['items']:
          bad_revisions.append(item['revision'])

  return get_highest_stable_revision(eligible_revisions, stable_build_revisions, bad_revisions)

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print "Error: No view URL supplied!\nUsage:\n%s URL" % sys.argv[0]
    sys.exit(1)
  print "Last stable revision: %d" % find_revision(sys.argv[1], verbose=True)