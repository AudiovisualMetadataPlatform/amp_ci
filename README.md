# amp_ci
Github webhooks server for continuous integration

NOTE: This is used internally by IU Libraries to build the AMP packages on repository changes.
The daemon is running on capybara

As with all of our services it is managed via iul_service and is being monitored by nagios.

## How it works
The AudiovisualMetadataPlatform account has been configured to send webhook push requests to our servers
when a repository has been modified.  These settings can be seen at 
https://github.com/organizations/AudiovisualMetadataPlatform/settings/hooks

When a push request comes in, it is compared to the list of repos in amp.yaml and if it matches, the
amp_bootstrap and the requested repo are checked out to a temporary directory.  The branch information
is compared in the scripts section of amp.yaml and if it doesn't match, the scripts listed in '*' will
be used (This has not been tested extensively).  The scripts are called in order which does the build
and package distribution.  If there are any failures in the scripts the process stops.

Logging is done in the installation's logs directory -- a log for each repository build and one for
the listener itself.

On successful builds the logging is minimal:
```
2023-09-12 19:13:05,359 [webhook_listener:webhook_listener.py:125] [INFO] [2541932] Building amppd, refs/heads/AMP-2926_acJob
2023-09-12 19:13:21,568 [webhook_listener:webhook_listener.py:156] [INFO] [2541932] Done building amppd, refs/heads/AMP-2926_acJob in 16.208548545837402 seconds
```

If the build fails for some reason the entirety of the script's stderr and stdout are included in the log.

Upon successful completion the packages should be copied to the test instance where they will be picked
up by drax and updated on that instance (if it is enabled).  When drax does the installation the amp team
is notified by email.

### amp_bootstrap is a special case
Since all of repositories have a soft dependency on amp_bootstrap, if a push request is received, all of the
known repositories are checked out and built.

## Troubleshooting
If a build fails for some reason, there are three ways to rebuild the package(s):
* Fix the problem and commit it to the repository.
* Go to the webhook configuration on github and redeliver the push appropriate push request
* Log into capybara and run the trigger_build script.

The last option is the best option when there was a transient error.
* Log into capybara, become the amp user, and change directory to the amp_ci installation dir
* `pipenv run trigger_build.py amp.yaml reponame`  (where reponame is the repository you want to rebuild)

a pointless change to trigger a message!

