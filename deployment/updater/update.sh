#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="/home/pi4/AI-Personal-Assistant"
DEPLOY_DIR="/home/pi4/echomind-deploy"
RELEASES_DIR="$DEPLOY_DIR/releases"
SHARED_DIR="$DEPLOY_DIR/shared"
CURRENT="$DEPLOY_DIR/current"
STATUS_FILE="$DEPLOY_DIR/update.status"

REPO="git@github.com:Thilinapri/AI-Personal-Assistant.git"
BRANCH="main"
SERVICE="echomind"
PYTHON="$APP_DIR/venv/bin/python"
READY_MARKER="Assistant Ready"
START_TIMEOUT=120

write_status() {
    printf '%s\n' "$1" > "$STATUS_FILE"
}

mkdir -p "$RELEASES_DIR"

# Prevent two updates from running simultaneously.
exec 9>"$DEPLOY_DIR/update.lock"
if ! flock -n 9; then
    echo "ERROR: Another update is already running."
    exit 1
fi

# Verify required shared resources.
for item in "$SHARED_DIR/.env" "$SHARED_DIR/memory.db" "$APP_DIR/venv/bin/python"; do
    if [[ ! -e "$item" ]]; then
        echo "ERROR: Required resource missing: $item"
        exit 1
    fi
done

if [[ ! -L "$CURRENT" ]]; then
    echo "ERROR: Current release link is missing."
    exit 1
fi

PREVIOUS=$(readlink -f "$CURRENT")

if [[ ! -f "$PREVIOUS/main.py" ]]; then
    echo "ERROR: Current release is invalid."
    exit 1
fi

write_status "checking"
echo "Checking GitHub..."
REMOTE_INFO=$(git ls-remote "$REPO" "refs/heads/$BRANCH")
COMMIT=$(awk 'NR==1 {print $1}' <<< "$REMOTE_INFO")

if [[ ! "$COMMIT" =~ ^[0-9a-f]{40}$ ]]; then
    echo "ERROR: Could not identify the latest commit."
    exit 1
fi

RELEASE="$RELEASES_DIR/$COMMIT"

if [[ "$RELEASE" == "$PREVIOUS" ]]; then
    echo "EchoMind is already running the latest commit: $COMMIT"
    write_status "uptodate"
    exit 0
fi

STAGING=""

cleanup() {
    if [[ -n "$STAGING" && -d "$STAGING" ]]; then
        rm -rf -- "$STAGING"
    fi
}
trap cleanup EXIT

# Download the release if it does not already exist.
if [[ ! -d "$RELEASE" ]]; then
    STAGING=$(mktemp -d "$RELEASES_DIR/.staging.XXXXXX")

    write_status "downloading"
    echo "Downloading commit: $COMMIT"
    git clone --quiet --depth 1 --branch "$BRANCH" "$REPO" "$STAGING"

    ACTUAL_COMMIT=$(git -C "$STAGING" rev-parse HEAD)

    if [[ "$ACTUAL_COMMIT" != "$COMMIT" ]]; then
        echo "ERROR: GitHub changed during download. Try again."
        exit 1
    fi

    mv "$STAGING" "$RELEASE"
    STAGING=""
else
    ACTUAL_COMMIT=$(git -C "$RELEASE" rev-parse HEAD)

    if [[ "$ACTUAL_COMMIT" != "$COMMIT" ]]; then
        echo "ERROR: Existing release has an unexpected commit."
        exit 1
    fi
fi

# Attach persistent resources without overwriting existing files.
ensure_link() {
    local path="$1"
    local target="$2"

    if [[ -L "$path" ]]; then
        if [[ "$(readlink "$path")" != "$target" ]]; then
            echo "ERROR: Incorrect existing symlink: $path"
            exit 1
        fi
    elif [[ -e "$path" ]]; then
        echo "ERROR: Refusing to overwrite existing file: $path"
        exit 1
    else
        ln -s "$target" "$path"
    fi
}

mkdir -p "$RELEASE/data"

ensure_link "$RELEASE/.env" "$SHARED_DIR/.env"
ensure_link "$RELEASE/data/memory.db" "$SHARED_DIR/memory.db"
ensure_link "$RELEASE/venv" "$APP_DIR/venv"

echo "Validating release..."
"$PYTHON" -m compileall -q "$RELEASE/src" "$RELEASE/main.py"

(
    cd "$RELEASE"
    ./venv/bin/python -c "import main; print('Release import OK')"
)

echo "Release validated: $COMMIT"
echo "Previous release: $PREVIOUS"

# Switch current using an atomic symlink replacement.
switch_current() {
    local target="$1"
    local temporary="$DEPLOY_DIR/.current.next.$$"

    rm -f "$temporary"
    ln -s "$target" "$temporary"
    mv -Tf "$temporary" "$CURRENT"
}

# Start service and wait for the actual application-ready message.
wait_for_ready() {
    local started_at
    started_at=$(date '+%Y-%m-%d %H:%M:%S')

    sudo systemctl start "$SERVICE"

    for ((i=0; i<START_TIMEOUT/2; i++)); do
        if ! sudo systemctl is-active --quiet "$SERVICE"; then
            echo "Service stopped unexpectedly during startup."
            return 1
        fi

        if sudo journalctl -u "$SERVICE" \
            --since "$started_at" -o cat --no-pager 2>/dev/null |
            grep -F "$READY_MARKER" >/dev/null; then

            if sudo systemctl is-active --quiet "$SERVICE"; then
                echo "Application readiness confirmed."
                return 0
            fi
        fi

        sleep 2
    done

    echo "ERROR: Application did not become ready in time."
    return 1
}

# Stop the old application before changing the active release.
write_status "installing"
echo "Stopping EchoMind..."
sudo systemctl stop "$SERVICE"

echo "Activating new release..."
switch_current "$RELEASE"

echo "Starting new release..."
if wait_for_ready; then
    write_status "success"
    echo
    echo "======================================"
    echo "UPDATE SUCCESSFUL"
    echo "Active commit: $COMMIT"
    echo "======================================"
    exit 0
fi

# Automatic rollback.
echo
write_status "rollback"
echo "UPDATE FAILED. Rolling back..."
sudo systemctl stop "$SERVICE" || true

switch_current "$PREVIOUS"

if wait_for_ready; then
    write_status "rolledback"
    echo "Rollback successful."
    echo "Restored release: $PREVIOUS"
else
    write_status "failed"
    echo "CRITICAL: Previous release did not become ready."
    echo "Inspect: sudo journalctl -u $SERVICE -n 100 --no-pager"
fi
exit 1
