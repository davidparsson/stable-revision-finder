#!/usr/bin/python
import ast
import urllib
import sys

def parse(url, tree=None):
  url = "%s/api/python" % url
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

def get_highest_stable_revision(eligible_revisions, good_revisions, bad_revisions):
  def find_closest_previous_revision(revision, sequence):
    return max(filter(lambda x: x <= revision, sequence))
        
  def no_failures_since_last_stable(previous_stable_revision, eligible_revision, bad_revisions):
    for revision in range(previous_stable_revision, eligible_revision):
      if revision in bad_revisions:
        return False
    return True
  
  eligible_revisions = clean_and_sort(eligible_revisions)
  bad_revisions = clean_and_sort(bad_revisions)
  
  for eligible_revision in eligible_revisions:
    if not eligible_revision in bad_revisions:
      for job_name in good_revisions:
        good_job_revisions = clean_and_sort(good_revisions[job_name])
        previous_stable_revision = find_closest_previous_revision(eligible_revision, good_job_revisions)
        if no_failures_since_last_stable(previous_stable_revision, eligible_revision, bad_revisions):
          return eligible_revision
  print -1

def find_revision():
  if len(sys.argv) < 2:
    print "Error: No view URL supplied!\nUsage:\n%s URL" % sys.argv[0]
    sys.exit(1)
  view_details = parse(sys.argv[1], "jobs[name,url]")

  good_revisions = {}
  eligible_revisions = []
  bad_revisions = []
  for job in view_details['jobs']:
    print "Finding stable revisions for %s..." % job['name']
    result = parse(job['url'], "builds[building,result,changeSet[items[revision]]]")
  
    current_good_revisions = []
    good_revisions[job['name']] = current_good_revisions
  
    for build in result['builds']:
      if not build['building'] and build['result'] == 'SUCCESS':
        for item in build['changeSet']['items']:
          current_good_revisions.append(item['revision'])
          eligible_revisions.append(item['revision'])
      else:
        for item in build['changeSet']['items']:
          bad_revisions.append(item['revision'])

  print
  print "Last stable revision:"
  print get_highest_stable_revision(eligible_revisions, good_revisions, bad_revisions)

if __name__ == '__main__':
  find_revision()