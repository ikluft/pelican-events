# Test data directories

The test_300* and test_500* test scripts point into here due to a symbolic link. The scripts will look in here for a directory with the same name as the test function, which also point to the same directory due to a symlink. They arrive here as follows:

* test_300_ical.py uses t300/test_generate_ical_file
* test_500_integ.py uses t500/test/run

The reason to do this is to have both scripts run tests on the same data from different levels of the code, one as a unit test that can see the internals and one as an integration test which runs it from the command-line interface without access to the internals.
