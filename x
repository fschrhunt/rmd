#!/bin/sh
# Offline repository checks; tests mock ExifTool and only use temporary files.
set -eu
cd "$(dirname "$0")"

# Help succeeds; unsupported commands and extra arguments exit 2.
usage() {
    echo 'usage: ./x [check|lint|test|shell|--help]' >&2
    echo 'check (default): syntax/indentation, shell syntax, and unittest; test accepts unittest arguments' >&2
    exit "${1:-2}"
}
command=${1-check}
if [ "$#" -gt 0 ]; then shift; fi
case "$command" in
    check)
        [ "$#" -eq 0 ] || usage
        ./x lint
        ./x shell
        ./x test
        ;;
    lint)
        [ "$#" -eq 0 ] || usage
        python3 - <<'PY'
# Compile source in memory and check ambiguous indentation without writing bytecode.
from pathlib import Path
import io
import tabnanny
import tokenize

for path in sorted([*Path('rmd').glob('*.py'), *Path('tests').glob('*.py')]):
    source = path.read_text(encoding='utf-8')
    compile(source, str(path), 'exec')
    tabnanny.process_tokens(tokenize.generate_tokens(io.StringIO(source).readline))
print('Python syntax and indentation: passed')
PY
        ;;
    test)
        if [ "$#" -eq 0 ]; then set -- discover -s tests -v; fi
        PYTHONDONTWRITEBYTECODE=1 python3 -m unittest "$@"
        ;;
    shell)
        [ "$#" -eq 0 ] || usage
        sh -n x
        ;;
    -h|--help|help)
        [ "$#" -eq 0 ] || usage
        usage 0
        ;;
    *) usage ;;
esac
