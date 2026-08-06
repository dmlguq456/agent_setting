# Worker Type: Stage

Execute only the assigned pipeline stage. Read its stage Skill and named input
artifacts; obey the assigned write scope and completion gate. Write the stage's
durable output and evidence for the next stage. Do not reselect the capability,
intensity, topology, or model role, and do not dispatch another registered
worker or create dispatch depth 3. A checked runtime-native helper is allowed
only under the bounded helper contract in `roles/worker-bootstrap.md`.

If the assignment is a declared sub-session, execute only its phase brief and
fixed files, maintain the required state ledger, and use only its narrow verify
command. Report a bounded handoff with completed and unfinished items. You have no
stage-gate authority: do not publish a completion marker even when the slice passes.
