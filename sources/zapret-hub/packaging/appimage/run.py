"""AppImage entry point, run by AppRun with the bundled Python in isolated mode.

Nothing in the environment points into the AppImage mount: Telegram, the
browser or TG WS Proxy that we start keep working after we exit and the mount
goes away. Python finds its libraries through RUNPATH, Qt through $ORIGIN."""

import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, HERE)

# the bundled OpenSSL looks for CA certificates where Fedora keeps them;
# point it at the system's own bundle, which outlives us
CA_FILES = ["/etc/ssl/certs/ca-certificates.crt", "/etc/pki/tls/certs/ca-bundle.crt",
            "/etc/ssl/ca-bundle.pem", "/etc/ssl/cert.pem", "/etc/pki/tls/cert.pem"]
if not os.environ.get("SSL_CERT_FILE"):
    found = next((p for p in CA_FILES if os.path.isfile(p)), None)
    os.environ["SSL_CERT_FILE"] = found or os.path.join(HERE, "..", "..", "..", "opt", "_internal", "certs.pem")

from zaprethub.__main__ import main  # noqa: E402

sys.exit(main())
