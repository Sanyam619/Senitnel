Protocol Notes (userspace NFSv4.2 emulation)
============================================

This rig emulates a very small slice of NFSv4.2 in userspace to study
what a single reboot does to in-flight state. It is not a production
server. The specific behaviours worth knowing:

Boot epochs
-----------
Every RECLAIM_DELEG record carries `boot_epoch`. On the previous boot
the server issued write/read delegations under `boot_epoch_prev`. On
restart the server bumps to `boot_epoch_curr`. A reclaim record from
a client is considered valid for the new epoch only if the record's
`boot_epoch` equals `boot_epoch_curr` (client re-established the
delegation inside the grace window) — otherwise the record is a
history entry from before the reboot and the reclaim did not complete
in time.

Client delegation records (DELEGATION_HELD) also carry a `boot_epoch`.
The client writes this record when it believes it holds a delegation
under that epoch. The client cannot know whether the server actually
reclaimed successfully until it reads back the server log post-reboot.

Reclaim grace window
--------------------
The server accepts reclaim records only for `grace_window_ms`
milliseconds after `boot_epoch_curr` begins. Any DELEGATION_HELD
record on the client whose stateid the server has NOT reclaimed under
`boot_epoch_curr` before the grace window closes is silently invalid.

Two-client conflicting delegations
----------------------------------
The rig lets two clients reclaim write delegations on the same file
handle during the grace window if both requests arrive before the
window closes. The rig's post-grace-window pass then serialises them:
the client with the numerically smaller `client_id` keeps its write
delegation, the other client's write delegation is downgraded to a
share reservation. Byte order for the compare is memcmp on the 16-byte
identifier.

Server-side COPY (RFC 7862)
---------------------------
The server initiates a COPY by writing a COPY_SESSION intent record and
the client emits a matching COPY_ISSUE. On successful commit the server
writes a COMMIT_SEAL whose `write_verifier` bytes match the intent's
`write_verifier`. If the reboot cut into the middle of a COPY the intent
may be present with `committed_flag=0` and a `bytes_flushed` below
`total_bytes`, and the server log will contain no matching COMMIT_SEAL.

Rename semantics
----------------
A RENAME record from a client is `delegation_backed=1` if the client
issued the rename against a live write delegation on `src_fh`. An
unbacked rename (`delegation_backed=0`) either succeeded pre-reboot on
the server side (visible as NAMESPACE_OP in the server log with the
same src/dst) or was lost. The rig only records unbacked renames when
the server acknowledged them before the reboot.
