# GitHub Paint
yet another CLI to draw text in your GitHub contributions graph.

## Usage

1. Fork this repository
2. Replace the `user` and `text` variables in [`.github\workflows\cron.yml`](.github\workflows\cron.yml)

## Development

### Prerequisites

* [`python`](https://www.python.org/downloads/)
* [`gh` cli](https://cli.github.com/)

### Clone the repo:

```bash
git clone https://github.com/tbrockman/github-paint
```

### Create a virtual environment:
```bash
python -m venv env
```

### Activate the environment:

#### Linux/MacOS
```bash
source env/bin/activate
```

#### Windows
```powershell
./env/Scripts/activate.ps1
```

### Install the dependencies:

```bash
pip install -r requirements.txt
```

### Run the CLI:

<!-- > [!NOTE]
> See [creating a personal access token (classic)](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic) for generating the personal access token -->

```bash
python -m src.main --help
```