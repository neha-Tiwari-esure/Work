# TODO

- Replace the temporary personal Test Analytics token with a dedicated QA user profile and credentials or JWT token.
- Move auth handling away from ad hoc personal access and document the stable QA-user setup.
- After QA-user auth is in place, re-run the extractor and verify the workbook output still matches live Test Analytics data.
- Confirm the intended Claims Core exact `run_name` list for routine use.
- Investigate why `Regression_Claims_HOME` is not present in the currently discovered sprint batches, or confirm that its absence is expected.
- Decide whether missing exact `run_name` values should keep producing empty workbooks or should fail the run.

<!-- -------
1. half working
cleanup the sheet based on
modify the workbook_writer.py to dump everything in one file -- write in next line
sprint strat and end date -> 2 weeks window plan

 -->
