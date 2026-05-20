# TODO

- Replace the temporary personal Test Analytics token with a dedicated QA user profile and credentials or JWT token.
- Move auth handling away from ad hoc personal access and document the stable QA-user setup.
- After QA-user auth is in place, re-run the extractor and verify the workbook output still matches live Test Analytics data.
- Confirm the intended Claims Core exact `run_name` list for routine use.
- Investigate why `Regression_Claims_HOME` is not present in the currently discovered sprint batches, or confirm that its absence is expected.
- Decide whether missing exact `run_name` values should keep producing empty workbooks or should fail the run.

<!-- DONE -->

 <!-- 
 TODO: 18th May
 Must have:
 1. Append the best of sprint to final file passed, failed, not analysed -- match the format based on existing @neha DONE
 2. Create a groovy script for posting updates on slack? --> insight on pass% increased-decreased or constant @sandra
 3. Make extractions and data dumping faster @neha
 4. Accessing JIRA for defect linking @sandra 

 Good to have:
 1. Known failures --> do nothing || new failures --> highlight (not taggeg, tagged to a bug that is not closed) 
 2. Capture log for New Bugs --> critical errors 500/400/201 etc @neha DONE
 3. Cost of the run/query --> Token usage 
 
 Question: how can we use this info to help QAs analyse the failures quickly ?

 must have --> when to run? env issue, known issue, pass % dropped 
 1. rerun failed tests and repeat the good to have 1-2

 1: extract log? yes

  -->
