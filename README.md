# SPES on OpenFaaS

Local development environment for the SPES coursework project. Every team
member runs an identical minikube + OpenFaaS CE cluster on their own laptop.

## Repo layout

(Folders appear on GitHub as their owners commit their first files; empty
folders are not tracked by Git.)

- `Functions/`  demo Python functions + `stack.yaml` + build template
                (owner: A)


## Pinned software versions

Everyone MUST run these exact versions. Check with the provided command
and update this table only if the team agrees to upgrade together.

| Tool            | Version   | Check with              |
|-----------------|-----------|-------------------------|
| Docker Desktop  | v29.9.3   | `docker --version`      |
| minikube        | v1.39.0   | `minikube version`      |
| Kubernetes      | v1.31.0   | `kubectl get nodes`     |
| faas-cli        | v0.18.18  | `faas-cli version`      |
| OpenFaaS CE     | helm chart `openfaas/openfaas`, latest at install (25 Nov 2026) | `helm list -n openfaas` |
| Python          | 3.10+     | `python --version`      |
| Docker Hub      | free account; required to PUBLISH images, not to pull/deploy | https://hub.docker.com |

Note: faas-cli v0.18.18 has a bug where `faas-cli up` (the BUILD step) fails
on Windows. macOS/Linux users can use `faas-cli up` normally; Windows users
follow the manual build steps in Section 6. Deploys work everywhere with
v0.18.18.

## 1. Prerequisites

- Windows 10/11, macOS (Intel or Apple Silicon) or Linux
- 2 CPUs, 4 GB free RAM and 20 GB free disk for the cluster
- A GitHub account (added as a collaborator on this repo)
- A free Docker Hub account (https://hub.docker.com) – only needed if you
  will publish images (Member A publishes the functions; each member will
  publish their own component later)

## 2. Install the tools

Install in the following order:

### Docker Desktop
- Windows: download from https://www.docker.com/products/docker-desktop/ ,
  tick "Use WSL 2" during install, restart if asked, then start Docker
  Desktop and wait until it reports running.
- macOS: download the correct build for your chip (Apple Silicon vs Intel).

### minikube
- Windows (PowerShell): `winget install Kubernetes.minikube`
  - Accept the source agreements on first run, then open a NEW terminal so
    PATH updates apply.
- macOS (Homebrew): `brew install minikube`
- Linux: follow https://minikube.sigs.k8s.io/docs/start/

Verify: `minikube version` prints v1.39.0.

### faas-cli
- macOS/Linux: `curl -sLS https://cli.openfaas.com | sh`
- Windows: download the exe directly:
  `curl.exe -LO https://github.com/openfaas/faas-cli/releases/latest/download/faas-cli.exe`
  (run from `C:\tools`, or add that folder to PATH)

### Git
- Windows: `winget install --id Git.Git -e --source winget`
  (this also installs Git Bash, which Windows users should use for faas-cli
  and general repo work; PowerShell is fine for kubectl/minikube)
- Configure once: `git config --global user.name "Your Name"` and
  `git config --global user.email "your-github-email"`

### Python
Install Python 3.10 or newer, then:
`pip install locust pandas`

## 3. Start the cluster

Docker Desktop must be running first. Then run this command:

```
minikube start --driver=docker --kubernetes-version=v1.31.0 --container-runtime=docker
```

Notes:
- Both flags are pinned deliberately so every laptop runs an identical
  cluster; do not "customise" your own.
- First start downloads ~800 MB of images; later starts take seconds.

Verify:

```
kubectl get nodes        # expect: minikube  Ready  control-plane
```

If `kubectl` is not on PATH, `minikube kubectl -- get nodes` is equivalent.

## 4. Install OpenFaaS CE

macOS/Linux (arkade):
```
curl -SLsf https://dl.get-arkade.dev/ | sh
arkade install openfaas
```
If arkade fails to extract helm on your platform, use helm directly
(this is what I did on Windows):
```
helm repo add openfaas https://openfaas.github.io/faas-netes/
helm repo update
helm upgrade openfaas --install openfaas/openfaas --namespace openfaas \
  --set functionNamespace=openfaas-fn --set generateBasicAuth=true
```
Windows notes for arkade:
- arkade needs `HOME` set in cmd: `set HOME=%USERPROFILE%` first.
- `arkade get faas-cli` does not support Windows; download the exe directly
  (see faas-cli above).

Verify all pods Running:
```
kubectl get pods -n openfaas
```
Expect: gateway, queue-worker, prometheus, nats, alertmanager, faas-idler,
basic-auth-plug. Prometheus is bundled with OpenFaaS and is the data source
for the SPES controller.

## 5. Access the gateway

The gateway must be port-forwarded; keep this running in a seperate
terminal (it does NOT survive a restart – re-run it every session):

```
kubectl port-forward -n openfaas svc/gateway 8080:8080
```

Web UI: http://127.0.0.1:8080 (user `admin`).

### Login (first time)

Get your cluster's auto-generated admin password (it is per-laptop, NOT
shared):

- macOS/Linux: `kubectl get secret -n openfaas basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode`
- Windows PowerShell:
  ```powershell
  $p = kubectl get secret -n openfaas basic-auth -o jsonpath="{.data.basic-auth-password}"
  [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($p))
  ```

Then: `faas-cli login --username admin --password-stdin` (pipe the decoded
password in, or run `faas-cli login` and paste when prompted).

Store the password in a password manager. NEVER commit it or share it.

## 6. Deploy the project functions

The function images are published on Docker Hub under
`mmendonca30/`, so NO local build is needed to deploy. From the
`Functions/` folder of this repo:

```
faas-cli deploy
```

Kubernetes pulls the published images automatically. Invoke one to confirm:

```
echo "test" | faas-cli invoke low-cpu-use
```

(The FIRST invoke of each function is slower: the cluster pulls the image
from Docker Hub. That is normal, and it is the cold start the project
studies. Second invocations are warm and fast.)

### Building a function (only when its code changes)

macOS/Linux: `faas-cli up` works normally, then push:

```
faas-cli up
docker tag low-cpu-use:latest mmendonca30/low-cpu-use:latest
docker push mmendonca30/low-cpu-use:latest
```

Windows: `faas-cli up` (v0.18.18) fails with
`unsupported protocol scheme "c"` (known bug: the template path is treated
as a URL). Build manually instead (PowerShell, in `Functions/`):

```powershell
$f = "low-cpu-use"   # repeat for each changed function
New-Item -ItemType Directory -Force -Path "build\$f\function" | Out-Null
Copy-Item "$f\handler.py" "build\$f\function\handler.py" -Force
Copy-Item "$f\requirements.txt" "build\$f\function\requirements.txt" -ErrorAction SilentlyContinue
Copy-Item "template\python3-http\requirements.txt" "build\$f\requirements.txt" -Force
Copy-Item "template\python3-http\Dockerfile" "build\$f\Dockerfile" -Force
Copy-Item "template\python3-http\index.py" "build\$f\index.py" -Force
docker build -t "$f`:latest" "build\$f"
docker tag "$f`:latest" "mmendonca30/$f`:latest"
docker push "mmendonca30/$f`:latest"
```

Then `faas-cli deploy` again.

Important build details:
- Builds run on the HOST Docker (do NOT apply `minikube docker-env` for
  this flow): images are distributed via Docker Hub, not local cluster
  images.
- The template's `requirements.txt` (which includes flask) must sit at the
  build-context ROOT; the function's own `requirements.txt` goes inside
  `function/`. Reversing these produces containers that crash with
  `No module named 'flask'`.
- OpenFaaS CE only deploys images it can verify as PUBLIC. Function images
  must live in public Docker Hub repositories. This is why images must
  never contain secrets or personal data (see Team rules).

## 7. Daily workflow

- Start: Docker Desktop running, `minikube start ...` (step 3),
  `kubectl port-forward -n openfaas svc/gateway 8080:8080`
- End: Ctrl+C the port-forward, then `minikube stop`
  (cluster state persists between stops)
- Code changes to functions: edit handler, build + push (Section 6),
  `faas-cli deploy`
- All repo changes via pull requests to `main`.

## Troubleshooting (things I had to troubleshoot)

- `minikube` not recognised after install: PATH only reloads in NEW
  terminal windows.
- `minikube start` hangs: check Docker Desktop is actually running first.
- arkade `Error: env-var HOME, not set` (Windows cmd): run
  `set HOME=%USERPROFILE%` in that window first.
- arkade fails extracting helm on Windows: use the manual helm commands
  above instead.
- `faas-cli up` on Windows fails with `unsupported protocol scheme "c"`:
  known v0.18.18 bug; use the manual build steps in Section 6.
- Deploy fails with `the Community Edition license agreement only allows
  public images`: the image name must point at a PUBLIC Docker Hub repo.
- Function pods in `CrashLoopBackOff`: check
  `kubectl logs -n openfaas-fn <pod-name>`. `No module named 'flask'`
  means the template requirements.txt was not at the build-context root
  (see Section 6).
- Invoke times out right after a deploy: the image is still being pulled
  from Docker Hub; wait and retry. Check pod status with
  `kubectl get pods -n openfaas-fn`.
- Gateway unreachable after restarting the laptop: the port-forward does
  not survive shutdowns; re-run it (Section 5).
- Windows Smart App Control blocks a downloaded faas-cli exe: use a
  version that runs; the security setting to override it is permanent, so
  prefer the working binary.
- Windows line endings breaking container entrypoints: this repo enforces
  LF via `.gitattributes`; do not override it in your editor.



