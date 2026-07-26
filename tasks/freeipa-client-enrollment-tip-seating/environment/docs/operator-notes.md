Operator notes
==============

ipahealth compares approximate entry counts between live per-host directories and
frozen keytab samples. Matching counts print joined. That probe does not read
keytab fingerprint continuity, realm preference, or SSSD abort windows.

Host names and fqdns live under /etc/ipa/hosts.list (name TAB fqdn). Service
principals and their host live under /etc/ipa/services.list (principal TAB host).
Site-standard preference tokens live under /app/config/site_standard.conf.
