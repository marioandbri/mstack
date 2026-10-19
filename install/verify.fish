#!/usr/bin/env fish
set script_dir (realpath (dirname (status filename)))
exec uv run --project "$script_dir" --locked python "$script_dir/mstack.py" verify $argv
