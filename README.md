# amp_ci
Github webhooks server for continuous integration

Based on adnanh/webhook on github

The webhook binary is from release 2.8.1

## Theory of operation.

Each github repository that needs to be built are set up with a webhook that
delivers push events in JSON format with the shared secret to the URL 
endpoint served by the webhook server.

As configured, the endpoint is something like:
```
https://<hostname>/webhook/amp_main
```

The webhook server is started/stopped by the `start_webhook.sh` and 
`stop_webhook.sh` scripts, respectively.

The webhook daemon listens to requests from github and will queue those requests
in the `queue` directory using the `queue_build.py` script.   The queue 
entry filename has the current timestamp (as a float) and consists of a JSON 
file with this structure:
``` 
{
    "repository": "Repository Name",
    "ref": "Commit ref",
    "commit_id": "Commit ID",
    "committer_name": "Committer Name",
    "committer_email": "Committer Email"
}
```

Periodically (via cron), the `build.py` script will scan the
queue and build those requests in the order they were made, possibly running
multiple builds concurrently.

The script to build the package is constructed by concatenating script chunks
from the `scripts` directory.  These chunks are always included:
* `checkout_repos`: clone the amp_bootstrap and the target repository and 
    check out the specific commit
* `build_packages`: set up the AMP build environment and run bootstrap's
    `amp_devel.py build <reponame>`

If there is a `distribute_<n>` script where `n` matches the last section of the
ref value (/refs/heads/main => main) it will also be included in the build.  

If the ref ends with `master`, it is a special case and it is coerced to `main`.
This script, if included, distributes the packages to their destination.

If the build fails the user that made the commit will receive an email with
the details, similar to:

```
Subject: AMP build failed for amp_mgms/84ce5aeb5cbfe12bf72096f34d93c9f5d148e997

Greetings and salutations bdwheele!

Hopefully this email finds you well.

The build for amp_mgms commit 84ce5aeb5cbfe12bf72096f34d93c9f5d148e997 in the branch refs/heads/main has failed.

The script returned an rc of 1 and produced the following output:
----------------------------------
<script output here>
----------------------------------

Sorry about that.

With warmest regards,
AMP CI
```

If the build is successful, no email will be sent.

## Logs

The `webhook.log` file is the log output of the webhook server.  It includes the
URLS which are called, which rules were matched, and the command lines of the
scripts which were called.

`build.log` is a unified log file for the build process.  It indicates the build
activity and if there is a build failure the script output is included.


## Configuration
Copy the `environment.sh-sample` file to `environment.sh` and modify the
value for `SECRET` to match the value used by the hook.

By default webhook will listen on `http://0.0.0.0:8196/webhook/{id}`  you will
need to mdify the start_webhook.sh script if your configuration differs.

The webhook server is started by running the `start_webhook.sh` script.  It can
be stopped with `stop_webhook.sh`.  

The default configuration has a single hood configured:  amp_main.  This hook
will run the queue_build.py script which will put the build request into a queue.

The queue is serviced by `build.py` which should be placed into the appropriate
user's crontab thusly:
```
* * * * * /path/to/build.py --threads <however many concurrent builds>
```

Each repository that is to be build should have a webhook which calls this
server using the id `amp_main`, a content type of application/json, and a 
secret matching the one set in environment.sh.

After that it should Just Work(tm)
