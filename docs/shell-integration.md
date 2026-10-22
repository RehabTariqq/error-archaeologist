# Shell integration

Run any command through Error Archaeologist so a failure automatically
searches your saved fixes.

## PowerShell

Open your profile:

```powershell
notepad $PROFILE
```

(If it does not exist: `New-Item -Path $PROFILE -ItemType File -Force`.)

Add this function, then restart PowerShell:

```powershell
function ea-run {
    ea run -- @args
}
```

Usage:

```powershell
ea-run python my_script.py
ea-run npm test
```

## Bash / Zsh

Add to `~/.bashrc` or `~/.zshrc`:

```bash
ea-run() { ea run -- "$@"; }
```

## Search whatever you just copied

Copy an error message (or a whole traceback) and run:

```bash
ea search --clip
```

For a traceback, the final error line is used for the search.

## Install the `ea` command

```bash
pip install .
```

Or, to keep editing the source:

```bash
pip install -e .
```

An installed copy stores cases in your user data folder
(`%APPDATA%\error-archaeologist` on Windows, `~/.local/share/error-archaeologist`
on Linux). A source checkout keeps using `data/cases.json`. Set
`ERROR_ARCHAEOLOGIST_DATA` to choose any other file.
