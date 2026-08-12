# rmd

`rmd` makes a cleaned copy of a file and removes the embedded metadata that [ExifTool](https://exiftool.org/) can write. It is intended for the simple terminal workflow: type `rmd `, drag one or more files into the terminal, and press Enter.

```console
$ rmd ~/Downloads/photo.jpg
Cleaned: /Users/me/Downloads/photo.jpg -> /Users/me/Downloads/photo.cleaned.jpg
```

Original files are never changed unless you explicitly use `--in-place`.

## Install

rmd requires Python 3.9+ and ExifTool.

```bash
# macOS
brew install exiftool pipx

pipx install rmd
```

Until the package is published, install directly from GitHub instead:

```bash
pipx install git+https://github.com/fschrhunt/rmd.git@metadata-cli
```

Or, from a checkout:

```bash
python3 -m pip install .
```

## Use

```bash
# Drag a file into your terminal after typing `rmd `
rmd photo.jpg

# Clean several files
rmd photo.jpg clip.mp4 document.pdf

# Preview work without writing files
rmd --dry-run photo.jpg

# Traverse a folder
rmd --recursive ./to-share

# Replace originals only after a successful cleanup
rmd --in-place photo.jpg
```

Use `rmd --help` for all options.

## What “remove metadata” means

rmd delegates metadata removal to ExifTool (`-all=`). This covers many image, video, audio, PDF, and document formats. ExifTool determines whether a particular format can be rewritten; rmd reports a failure and leaves the original alone when it cannot.

Not every privacy risk is file metadata. In particular, rmd does **not** redact visible text, faces, GPS coordinates printed in an image, document revision content, hidden layers, embedded files, web-page scripts, or tracking information inside the file's actual content. Review a cleaned result before sharing sensitive material.

## Development

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT
