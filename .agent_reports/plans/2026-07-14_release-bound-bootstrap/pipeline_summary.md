# Pipeline summary — release-bound bootstrap

## Current state

Complete. Commit `b85a95d7` was fast-forwarded to `main`, `v1.0.1` published
four assets, and the public latest installer passed checksum, exact binding,
all-runtime strict doctor, and managed update verification in an isolated HOME.

## Contract change

Public installation is now one immutable `repository@tag` transaction:

1. GitHub latest or versioned Release selects `install.sh`.
2. That installer contains distribution code from the same Git ref.
3. It requests only its embedded repository and tag.
4. The archive checksum, extraction, activation, pointer commit, and rollback
   remain the existing managed-release transaction.

The former raw-main URL remains only as a compatibility redirect to step 1.
