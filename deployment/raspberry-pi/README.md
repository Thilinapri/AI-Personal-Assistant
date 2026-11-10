# EchoMind Raspberry Pi Deployment

These systemd templates start the EchoMind Python backend and Next.js dashboard automatically at boot.

## 1. Prepare the Pi

Use the feature/cloud-reminder-sync branch.

Install the required Python dependencies and a compatible Node.js version.

The project needs:
- A Python virtual environment at .venv
- Python dependencies from requirements.txt
- Node.js 20.9 or newer
- Next.js dependencies installed with npm ci
- A successful Next.js production build
- Local .env and frontend/echomind-dashboard/.env.local configuration
- A working microphone

Never commit credentials.

## 2. Discover the Pi paths

From the repository root, run:

whoami
pwd
command -v npm
dirname "$(command -v node)"

Record the results.

## 3. Configure the service templates

Replace:

__PI_USER__ with the Pi username
__REPO_DIR__ with the absolute repository path
__NPM_BIN__ with the absolute npm executable path
__NODE_BIN_DIR__ with the Node.js binary directory

The Python service expects:
__REPO_DIR__/.venv/bin/python

## 4. Install services

Copy the configured service files into:

/etc/systemd/system/

Then run:

sudo systemctl daemon-reload
sudo systemctl enable --now echomind-backend.service
sudo systemctl enable --now echomind-dashboard.service

## 5. Verify

sudo systemctl status echomind-backend
sudo systemctl status echomind-dashboard

View logs with:

journalctl -u echomind-backend -n 50 --no-pager
journalctl -u echomind-dashboard -n 50 --no-pager

## 6. Access dashboard

Find the Pi IP:

hostname -I

On a laptop connected to the same network, open:

http://PI-IP:3000

Use a trusted private network. The dashboard is not designed for public internet exposure.

## 7. Final testing

Reboot the Pi and confirm both services start.

Test microphone capture, speech transcription, memory operations, dashboard access, and cloud reminder synchronization.

Keep Supabase reminder delivery Cron disabled except during controlled tests.
