Operator notes
==============

ldaphealth compares approximate entry counts between live database directories
and frozen LDIF samples. Matching counts print in-sync. That probe does not
read contextCSN continuity, prefer selection, or hold windows.

Roster names and suffixes live under /etc/ldap/roster.list (name TAB suffix).
Site-standard prefer tokens live under /app/config/site_standard.conf.
