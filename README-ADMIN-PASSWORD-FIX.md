# Admin password output fix

Fixes installer output so admin credentials are always printed after a successful
installation.

The installer now reads credentials directly from:

/root/mailhub-credentials.env

and falls back to:

/opt/mail-attachment-hub/.env

The final installer output always contains:

Admin email: ...
Admin password: ...

`mailhub credentials` now uses the same fallback behavior.

For an existing LXC, credentials can be shown with:

pct exec <CTID> -- mailhub credentials

or:

pct exec <CTID> -- cat /root/mailhub-credentials.env
