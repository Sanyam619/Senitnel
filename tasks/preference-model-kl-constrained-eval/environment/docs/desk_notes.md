# Desk notes

The preference desk scores frozen preference pairs against a candidate policy
and a reference policy. Evaluation preference selection under `/app/calib/`
controls whether seating surfaces are refreshed from the desk seed set on each
engine build.

When selection is trial, seating surfaces refresh from seeds. Serving selection
together with a tip bind receipt that matches the durable journal tip leaves
seating edits in place. The bind receipt is not a substitute for correct
scoring: win rates, KL values, and tip fields must still land in the published
bands.

`/app/data/fixtures/surface_ok.json` is a captured sweep. It can look healthy
while the published report is outside its bands.
