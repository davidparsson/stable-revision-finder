#!/usr/bin/python
import ast
import urllib
import sys
import optparse

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

def is_stable_revision(eligible_revision, stable_revisions_by_job, bad_revisions):
  for stable_job_revisions in stable_revisions_by_job.values():
    stable_job_revisions = clean_and_sort(stable_job_revisions)
    previous_stable_revision = find_closest_previous_revision(eligible_revision, stable_job_revisions)
    if failures_since_last_stable(previous_stable_revision, eligible_revision, bad_revisions):
      return False
  return True

def get_highest_stable_revision(eligible_revisions, stable_revisions_by_job, bad_revisions):
  eligible_revisions = clean_and_sort(eligible_revisions)
  bad_revisions = clean_and_sort(bad_revisions)

  for eligible_revision in eligible_revisions:
    if not eligible_revision in bad_revisions:
      if is_stable_revision(eligible_revision, stable_revisions_by_job, bad_revisions):
        return eligible_revision
  return -1

def find_revision(url, verbose=False):
  view_details = parse(url, "jobs[name,url]")

  stable_revisions_by_job = {}
  eligible_revisions = []
  bad_revisions = []
  for job in view_details['jobs']:
    if verbose:
      print "Querying %s..." % job['name']
    result = parse(job['url'], "builds[building,result,changeSet[items[revision]]]")

    current_job_stable_revisions = []
    stable_revisions_by_job[job['name']] = current_job_stable_revisions

    for build in result['builds']:
      if not build['building'] and build['result'] == 'SUCCESS':
        for item in build['changeSet']['items']:
          current_job_stable_revisions.append(item['revision'])
          eligible_revisions.append(item['revision'])
      else:
        for item in build['changeSet']['items']:
          bad_revisions.append(item['revision'])

  return get_highest_stable_revision(eligible_revisions, stable_revisions_by_job, bad_revisions)

def main():
  parser = optparse.OptionParser(usage="""Usage: %prog VIEW_URL [options]

Gets the highest common revision for all jobs in the supplied Jenkins view.""")
  parser.add_option("-v", "--verbose", help="Prints progress, instead of only the revision", action="store_true", default=False)
  try:
    (options, (url,)) = parser.parse_args()
    revision = find_revision(url, verbose=options.verbose)
    if options.verbose:
      print "Last stable revision: %d" % revision
    else:
      print revision
    return 0
  except ValueError:
    parser.print_help()
    return 1

if __name__ == '__main__':
  sys.exit(main())
