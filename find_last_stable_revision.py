#!/usr/bin/python
import ast
import urllib
import sys
import optparse

class RevisionStatuses():

  STABLE = True
  UNSTABLE = False

  def __init__(self):
    self._revision_results = {}

  def add_stable_revision(self, revision):
    self._revision_results[revision] = self.STABLE

  def add_unstable_revision(self, revision):
    self._revision_results[revision] = self.UNSTABLE

  def is_revision_stable(self, revision):
    while revision > 0:
      if revision in self._revision_results.keys():
        return self._revision_results[revision]
      revision -= 1
    return None


def parse(url, tree=None):
  if url[-1] != "/":
    url += "/"
  url = "%sapi/python" % url
  if tree:
    url += "?tree=%s" % tree
  return ast.literal_eval(urllib.urlopen(url).read())

def is_stable_revision(eligible_revision, revisions_by_job):
  any_stable = False
  for revision_statuses in revisions_by_job.values():
    stable = revision_statuses.is_revision_stable(eligible_revision)
    if stable is not None:
      if not stable:
        return False
      any_stable = True
  return any_stable

def get_highest_stable_revision(eligible_revisions, revisions_by_job):
  eligible_revisions.sort(reverse=True)
  for eligible_revision in eligible_revisions:
    if is_stable_revision(eligible_revision, revisions_by_job):
      return eligible_revision
  return -1

def find_revision(url, verbose=False):
  view_details = parse(url, "jobs[name,url]")

  revisions_by_job = {}
  eligible_revisions = []
  for job in view_details['jobs']:
    if verbose:
      print "Querying %s..." % job['name']
    result = parse(job['url'], "builds[building,result,changeSet[items[revision]]]")

    revision_statuses = RevisionStatuses()
    revisions_by_job[job['name']] = revision_statuses

    for build in result['builds']:
      if not build['building'] and build['result'] == 'SUCCESS':
        for item in build['changeSet']['items']:
          revision = item['revision']
          revision_statuses.add_stable_revision(revision)
          eligible_revisions.append(revision)
      else:
        for item in build['changeSet']['items']:
          revision_statuses.add_unstable_revision(item['revision'])

  return get_highest_stable_revision(eligible_revisions, revisions_by_job)

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
