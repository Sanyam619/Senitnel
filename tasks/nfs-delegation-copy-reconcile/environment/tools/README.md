Operator tools:
- inspect.c — reads an episode directory and dumps each journal file
  in plain text. Built at image build time to bin/nfsr-inspect.
- reconcile.c — recovery entry point used by the site recovery pass;
  the Makefile provides a build target for it.
