#!/usr/bin/python
import ast
import urllib
import sys
import argparse
import re
import sys
from datetime import datetime

verbose = False
debug = False

class RevisionStatuses():

    STABLE = 1
    BUILDING = 2
    NOT_BUILT = 3
    UNSTABLE = 4

    def __init__(self):
        self._revision_results = {}

    def add_stable_revision(self, revision):
        self._revision_results[revision] = self.STABLE

    def add_unstable_revision(self, revision):
        if self._revision_results.get(revision) != self.STABLE:
            self._revision_results[revision] = self.UNSTABLE

    def add_building_revision(self, revision):
        self._revision_results[revision] = self.BUILDING

    def is_revision_stable(self, revision):
        while revision > 0:
            if revision in self._revision_results.keys():
                return self._revision_results[revision] == self.STABLE
            revision -= 1
        return None

    def get_status_for(self, revision):
        return self._revision_results.get(revision, self.NOT_BUILT)

    def get_status_as_text_for(self, revision):
        dictionary = { self.STABLE: "STABLE",
                       self.UNSTABLE: "UNSTABLE",
                       self.BUILDING: "BUILDING",
                       self.NOT_BUILT: "NOT BUILT" }
        return dictionary[self.get_status_for(revision)]


def parse(url, tree=None):
    if url[-1] != "/":
        url += "/"
    url = "%sapi/python" % url
    if tree:
        url += "?tree=%s" % tree
    print_if_debug("Parsing %s" % url)
    return ast.literal_eval(urllib.urlopen(url).read())


def is_stable_revision(eligible_revision, revisions_by_job):
    any_stable = False
    for job_name in revisions_by_job.keys():
        revision_statuses = revisions_by_job[job_name]
        stable = revision_statuses.is_revision_stable(eligible_revision)
        if stable is not None:
            if not stable:
                status = revision_statuses.get_status_as_text_for(eligible_revision)
                print_if_verbose("Revision %d is %s for %s!" % (eligible_revision, status, job_name))
                return False
            any_stable = True
    return any_stable


def get_highest_stable_revision(eligible_revisions, revisions_by_job):
    eligible_revisions.sort(reverse=True)
    for eligible_revision in eligible_revisions:
        if is_stable_revision(eligible_revision, revisions_by_job):
            return eligible_revision
    return -1

def get_timestamp_for_revision(view_details, revision):
    for job in view_details['jobs']:
        for build in job['builds']:
            for changeSetItem in build['changeSet']['items']:
                if changeSetItem['revision'] == revision:
                    return int(changeSetItem['timestamp']) / 1e3
    return -1

def get_age_of_revision(view_details, revision):
    revision_timestamp = get_timestamp_for_revision(view_details, revision)
    return datetime.now() - datetime.fromtimestamp(revision_timestamp)

def find_revision(url, include_patterns=[], exclude_patterns=[]):
    view_details = parse(url, "jobs[name,url,builds[building,result,changeSet[items[revision,timestamp]]]]")

    revisions_by_job = {}
    eligible_revisions = set()
    for job in view_details['jobs']:
        if not include_job(job['name'], include_patterns, exclude_patterns):
            print_if_verbose("Excluding %s" % job['name'])
            continue
        print_if_verbose("Checking %s..." % job['name'])
        revision_statuses = RevisionStatuses()
        revisions_by_job[job['name']] = revision_statuses

        for build in job['builds']:
            if build['building']:
                for item in build['changeSet']['items']:
                    revision_statuses.add_building_revision(item['revision'])
            elif build['result'] == 'SUCCESS':
                for item in build['changeSet']['items']:
                    revision = item['revision']
                    revision_statuses.add_stable_revision(revision)
                    eligible_revisions.add(revision)
            else:
                for item in build['changeSet']['items']:
                    revision_statuses.add_unstable_revision(item['revision'])
    revision = get_highest_stable_revision(list(eligible_revisions), revisions_by_job)
    return (revision, get_age_of_revision(view_details, revision))

def include_job(job_name, include_patterns, exclude_patterns):
    exclude = False
    include = False
    if include_patterns:
        for pattern in include_patterns:
            if re.match(pattern, job_name):
                include = True
    else:
        include = True
    for pattern in exclude_patterns:
        if re.match(pattern, job_name):
            exclude = True
    return include and not exclude


def get_second_url_with_first_host(from_url, to_url):
    from_host = split_after_host(from_url)[0]
    to_path = split_after_host(to_url)[1]
    return '%s/%s' % (from_host, to_path)

def split_after_host(url):
    single_slash_pattern = '(?<!/)/(?!/)'
    return re.split(single_slash_pattern, url, 1)

def print_if_verbose(message):
    if verbose or debug:
        print message

def print_if_debug(message):
    if debug:
        print message

def format_timedelta(timedelta):
    hours, remainder = divmod(timedelta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if timedelta.days:
        return "%dd %dh %dm" % (timedelta.days, hours, minutes)
    return "%dh %dm" % (hours, minutes)

def main():
    global verbose, debug
    parser = argparse.ArgumentParser(description="Gets the highest common stable revision for all jobs in the supplied Jenkins view.", formatter_class=argparse.RawDescriptionHelpFormatter)
    try:
        parser.add_argument("-v", "--verbose", help="Prints progress, instead of only the revision", action="store_true", default=False)
        parser.add_argument("-d", "--debug", help="Prints web requests", action="store_true", default=False)

        parser.add_argument('--include', default=[], nargs='+', help='Include pattern(s) in regex')
        parser.add_argument('--exclude', default=[], nargs='+', help='Exclude pattern(s) in regex')

        parser.add_argument("view_url", metavar="VIEW_URL")

        options = parser.parse_args()
        verbose = options.verbose
        debug = options.debug
        (revision, age) = find_revision(options.view_url, options.include, options.exclude)
        if verbose:
            print
            print "Last stable revision: %d" % revision
            print "Revision age: %s" % format_timedelta(age)
            print
            if age.days:
                print "WARNING: Revision is more than one day old!"
        else:
            print revision
        return 0
    except ValueError:
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main())
