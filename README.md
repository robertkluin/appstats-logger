AppStats Logger
===============
A simple middleware to dump a reduced form of the App Stats data to a log
record.  This makes doing analysis on the profiling data possible.

About
-----
This is a simple set of middlewares and a Recorder to collect a simplified
version of the App Stats data and dump it to a log record.  The data does not
include stack information, but it does provide timing and offset from
start of request, making it possible to produce the "graph" shown at the top
of the App Stats page.

The application consists of two main parts, the middleware and the recorder.
The recorder gets registered, using the App Stats tooling, with the SDK so
that it is called for each RPC.  The middleware ensure the requests get
registered and handle calling the recorder's dump method to emit the profile
data to the logs.


NOTICE
======
Requirements to commit here:
  - Branch off master, PR back to master.
  - Your code should pass [Flake8](https://github.com/bmcustodio/flake8).
  - Good docstrs are required.
  - Good [commit messages](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html) are required.

