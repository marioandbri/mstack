#!/usr/bin/env fish

argparse 'home=' 'repo=' -- $argv
or exit 2

set script_dir (realpath (dirname (status filename)))
set repo_root (realpath "$script_dir/..")
if set -q _flag_repo
    set repo_root (realpath "$_flag_repo")
end

set target_home $HOME
if set -q _flag_home
    if not test -d "$_flag_home"
        echo "ERROR home directory does not exist: $_flag_home" >&2
        exit 1
    end
    set target_home (realpath "$_flag_home")
end

set manifest "$repo_root/skills.json"
if not test -f "$manifest"
    echo "ERROR missing manifest: $manifest" >&2
    exit 1
end
if not command -q jq
    echo "ERROR jq is required" >&2
    exit 1
end

set skills (jq -r '.skills[].name' "$manifest")
set target_ids agents claude codex pi
set target_roots \
    "$target_home/.agents/skills" \
    "$target_home/.claude/skills" \
    "$target_home/.codex/skills" \
    "$target_home/.pi/agent/skills"
set errors 0
set checked 0

for skill in $skills
    set source "$repo_root/skills/$skill"
    for index in (seq (count $target_ids))
        set destination "$target_roots[$index]/$skill"
        set checked (math $checked + 1)
        if not test -L "$destination"
            echo "ERROR $target_ids[$index]/$skill is not a symlink" >&2
            set errors (math $errors + 1)
            continue
        end
        set resolved (realpath "$destination" 2>/dev/null)
        if test "$resolved" != "$source"
            echo "ERROR $target_ids[$index]/$skill resolves to $resolved" >&2
            set errors (math $errors + 1)
        end
    end
end

if test $errors -gt 0
    echo "FAIL checked=$checked errors=$errors" >&2
    exit 1
end

echo "PASS checked=$checked canonical skill links"
