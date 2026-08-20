#!/usr/bin/env fish

argparse 'apply' 'home=' 'repo=' -- $argv
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

set apply_mode false
if set -q _flag_apply
    set apply_mode true
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
if test (count $skills) -eq 0
    echo "ERROR manifest has no skills" >&2
    exit 1
end

set target_ids agents claude codex pi
set target_roots \
    "$target_home/.agents/skills" \
    "$target_home/.claude/skills" \
    "$target_home/.codex/skills" \
    "$target_home/.pi/agent/skills"

set timestamp (date -u +%Y%m%dT%H%M%SZ)
set backup_root "$target_home/.engineering-skills-backups/$timestamp-$fish_pid"
set backup_count 0
set link_count 0
set unchanged_count 0

if $apply_mode
    echo "MODE apply"
else
    echo "MODE dry-run"
end
echo "REPO $repo_root"
echo "HOME $target_home"

for skill in $skills
    set source "$repo_root/skills/$skill"
    if not test -f "$source/SKILL.md"
        echo "ERROR missing canonical skill: $source/SKILL.md" >&2
        exit 1
    end

    for index in (seq (count $target_ids))
        set target_id $target_ids[$index]
        set target_root $target_roots[$index]
        set destination "$target_root/$skill"

        set resolved ""
        if test -L "$destination"
            set resolved (realpath "$destination" 2>/dev/null)
        end

        if test "$resolved" = "$source"
            echo "OK $target_id/$skill"
            set unchanged_count (math $unchanged_count + 1)
            continue
        end

        set backup ""
        if test -e "$destination"; or test -L "$destination"
            echo "PLAN backup $destination"
            if $apply_mode
                set backup "$backup_root/$target_id/$skill"
                if not mkdir -p (dirname "$backup"); or not mv "$destination" "$backup"
                    echo "ERROR could not back up $destination" >&2
                    exit 1
                end
                set backup_count (math $backup_count + 1)
            end
        end

        echo "PLAN link $destination -> $source"
        if $apply_mode
            if not mkdir -p "$target_root"; or not ln -s "$source" "$destination"
                echo "ERROR could not link $destination" >&2
                if test -n "$backup"; and test -e "$backup"
                    mv "$backup" "$destination"
                    echo "RESTORED $destination" >&2
                end
                exit 1
            end
            set link_count (math $link_count + 1)
        end
    end
end

if $apply_mode
    echo "RESULT linked=$link_count unchanged=$unchanged_count backed_up=$backup_count"
    if test $backup_count -gt 0
        echo "BACKUP $backup_root"
    end
else
    echo "RESULT dry-run; no files changed"
end
