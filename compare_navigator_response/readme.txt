Steps to use these two scripts:

1.  Add query route API links in the test_routes.csv file
    - Note please make sure to enter all the values requested in the file. 
2.  Run save_response.py on current Navigator Code
    - This will create a .json file for all of the cases in test_routes.csv
3.  Deploy new navigator code
4.  Run compare_response.py
    - This will read each of the previously created .json files, then query the same route and compare differences
    in the link sequence, and voice instruction sequence
    - This will output route_comparison.
    - Route comparison fields stand for:
	-Test Results: Either same (no change), regressed(issue regressed), Check nav response (response changed and needs manual input), Weird old_status (means there is a typo in the test_routes.csv file status column), invalid route (means the link sequence changed, make sure both routes are tested at the same time)
	- Old Status: Refelcts the status in the input file
	- New Status: pass(test passed), fail(test failed), check(previous failed changed and needs manual checking), Invalid different routes (link sequence changed), weird old status (typo in the test-routes.csv file)
	-city: city of the route
	- Case: description of the navigator case
	- Instructions change: Shows the difference instruction or if they are the same
	- Route URL: Shows the URL for the route

Note that this is not completed and we can make it more advanced than it currently is
Just need feedback on what kind of differences we want to look for and what kind of output is most helpful.

Also to avoid getting different routes please be sure to get the routes at 2am to avoid any difference in the routes when doing the requests. 
