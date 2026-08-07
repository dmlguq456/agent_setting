#!/bin/sh
# Compatibility redirect for the former raw-main install URL.
# The public installer and its embedded distribution code live in one release.
set -eu

REPOSITORY=${HARNESS_REPOSITORY:-dmlguq456/hearting}
INSTALL_URL=${HARNESS_INSTALL_URL:-https://github.com/$REPOSITORY/releases/latest/download/install.sh}

case "$INSTALL_URL" in
  https://*) ALLOW_FILE=0 ;;
  file://*)
    if [ "${HARNESS_ALLOW_FILE_RELEASES:-0}" != "1" ]; then
      echo "hearting: installer URL must use HTTPS." >&2
      exit 1
    fi
    ALLOW_FILE=1
    ;;
  *)
    echo "hearting: installer URL must use HTTPS." >&2
    exit 1
    ;;
esac

TMP=$(mktemp -d "${TMPDIR:-/tmp}/hearting-redirect.XXXXXX")
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
INSTALLER="$TMP/install.sh"

if command -v curl >/dev/null 2>&1; then
  if [ "$ALLOW_FILE" = "1" ]; then
    curl -fsSL "$INSTALL_URL" -o "$INSTALLER"
  else
    curl -fsSL --proto '=https' --tlsv1.2 "$INSTALL_URL" -o "$INSTALLER"
  fi
elif command -v wget >/dev/null 2>&1; then
  if [ "$ALLOW_FILE" = "1" ]; then
    echo "hearting: file installer override requires curl." >&2
    exit 1
  fi
  wget -qO "$INSTALLER" "$INSTALL_URL"
else
  echo "hearting: curl or wget is required." >&2
  exit 1
fi

sh "$INSTALLER" "$@"
