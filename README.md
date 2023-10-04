# amp_ci
Github webhooks server for continuous integration

Based on adnanh/webhook on github

The webhook binary is from release 2.8.1

## Theory of operation.

The webhook daemon listens to requests from github and will queue those requests
in the `queue` directory.   Periodically, the `build.py` script will scan the
queue and build those requests in the order they were made, possibly running
multiple builds concurrently.

If the build fails the user that made the commit will receive an email with
the details.

All builds will include the `checkout_repos` and `build_packages` scripts. 
If the branch name matches a `distribute_*` script, it will also be used.
For sanity, the branch `master` is renamed `main` for the purpose of finding
the distribute script.


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
