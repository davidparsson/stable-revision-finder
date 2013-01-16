Stable Revision Finder
======================

Finds the latest common stable revision for all builds in a Jenkins view.

Useful for finding a commonly releasable revision across many different Jenkins jobs. 

Usage
-----
To get the latest stable revision, run:
<pre>
python find_last_stable_revision.py http://[jenkins host]/view/[view name]/
</pre>

If you want more details on what's going on, append the `--verbose` flag:
<pre>
python find_last_stable_revision.py http://[jenkins host]/view/[view name]/ --verbose
</pre>
