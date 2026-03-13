"""Unified diff parser for the SAP ABAP/UI5 Review Assistant.

Parses standard unified diff format (git diff output) into structured data
for targeted review of changed code.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class DiffLine:
    """A single line within a diff hunk."""

    type: str  # "added", "removed", "context"
    content: str
    old_line: int | None
    new_line: int | None


@dataclass
class DiffHunk:
    """A contiguous block of changes within a file diff."""

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[DiffLine] = field(default_factory=list)


@dataclass
class DiffFile:
    """A single file's diff, containing one or more hunks."""

    old_path: str
    new_path: str
    hunks: list[DiffHunk] = field(default_factory=list)
    is_binary: bool = False
    is_rename_only: bool = False

    @property
    def added_lines(self) -> list[str]:
        """Return only added line contents across all hunks."""
        result: list[str] = []
        for hunk in self.hunks:
            for line in hunk.lines:
                if line.type == "added":
                    result.append(line.content)
        return result

    @property
    def removed_lines(self) -> list[str]:
        """Return only removed line contents across all hunks."""
        result: list[str] = []
        for hunk in self.hunks:
            for line in hunk.lines:
                if line.type == "removed":
                    result.append(line.content)
        return result


# ---------------------------------------------------------------------------
# Hunk header regex: @@ -old_start,old_count +new_start,new_count @@
# ---------------------------------------------------------------------------

_HUNK_HEADER_RE = re.compile(
    r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@"
)


def parse_unified_diff(diff_text: str) -> list[DiffFile]:
    """Parse unified diff format (git diff output) into structured data.

    Handles:
    - Standard unified diff format (--- a/file, +++ b/file, @@ hunks)
    - Lines starting with +/- for added/removed
    - Context lines (no prefix)
    - Multiple files in one diff
    - Edge cases: binary files, rename-only, empty diff
    """
    if not diff_text or not diff_text.strip():
        return []

    files: list[DiffFile] = []
    lines = diff_text.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]

        # Look for diff file header: "diff --git a/... b/..."
        if line.startswith("diff --git "):
            diff_file, i = _parse_file_block(lines, i)
            if diff_file is not None:
                files.append(diff_file)
        # Also handle plain unified diffs without "diff --git" header
        elif line.startswith("--- "):
            diff_file, i = _parse_plain_file_block(lines, i)
            if diff_file is not None:
                files.append(diff_file)
        else:
            i += 1

    return files


def _parse_file_block(lines: list[str], start: int) -> tuple[DiffFile | None, int]:
    """Parse a single file block starting at a 'diff --git' line."""
    i = start
    git_line = lines[i]

    # Extract paths from "diff --git a/path b/path"
    match = re.match(r"diff --git a/(.*?) b/(.*?)$", git_line)
    if not match:
        return None, i + 1

    old_path = match.group(1)
    new_path = match.group(2)

    i += 1

    # Skip extended header lines (index, mode, similarity, rename, etc.)
    is_binary = False
    is_rename_only = True  # Assume rename-only until we see hunks

    while i < len(lines):
        line = lines[i]
        if line.startswith("Binary files"):
            is_binary = True
            i += 1
            return DiffFile(
                old_path=old_path,
                new_path=new_path,
                is_binary=True,
                is_rename_only=False,
            ), i
        if line.startswith("--- "):
            break
        if line.startswith("diff --git "):
            # Next file block starts — this was a rename/mode-only change
            return DiffFile(
                old_path=old_path,
                new_path=new_path,
                is_rename_only=True,
            ), i
        i += 1

    if i >= len(lines):
        return DiffFile(
            old_path=old_path,
            new_path=new_path,
            is_rename_only=True,
        ), i

    # Parse --- and +++ lines
    if i < len(lines) and lines[i].startswith("--- "):
        old_header = lines[i]
        old_path_from_header = _extract_path(old_header, "--- ")
        if old_path_from_header:
            old_path = old_path_from_header
        i += 1

    if i < len(lines) and lines[i].startswith("+++ "):
        new_header = lines[i]
        new_path_from_header = _extract_path(new_header, "+++ ")
        if new_path_from_header:
            new_path = new_path_from_header
        i += 1

    # Parse hunks
    hunks: list[DiffHunk] = []
    while i < len(lines):
        line = lines[i]
        if line.startswith("diff --git "):
            break
        hunk_match = _HUNK_HEADER_RE.match(line)
        if hunk_match:
            hunk, i = _parse_hunk(lines, i, hunk_match)
            hunks.append(hunk)
        else:
            i += 1

    diff_file = DiffFile(
        old_path=old_path,
        new_path=new_path,
        hunks=hunks,
        is_binary=is_binary,
        is_rename_only=len(hunks) == 0 and not is_binary,
    )
    return diff_file, i


def _parse_plain_file_block(
    lines: list[str], start: int
) -> tuple[DiffFile | None, int]:
    """Parse a plain unified diff block starting at '--- ' line."""
    i = start
    old_path = _extract_path(lines[i], "--- ") or ""
    i += 1

    new_path = ""
    if i < len(lines) and lines[i].startswith("+++ "):
        new_path = _extract_path(lines[i], "+++ ") or ""
        i += 1

    hunks: list[DiffHunk] = []
    while i < len(lines):
        line = lines[i]
        if line.startswith("diff --git ") or line.startswith("--- "):
            break
        hunk_match = _HUNK_HEADER_RE.match(line)
        if hunk_match:
            hunk, i = _parse_hunk(lines, i, hunk_match)
            hunks.append(hunk)
        else:
            i += 1

    return DiffFile(
        old_path=old_path,
        new_path=new_path,
        hunks=hunks,
    ), i


def _extract_path(header_line: str, prefix: str) -> str | None:
    """Extract file path from --- or +++ header lines."""
    rest = header_line[len(prefix) :].strip()
    if rest == "/dev/null":
        return "/dev/null"
    # Remove a/ or b/ prefix
    if rest.startswith("a/") or rest.startswith("b/"):
        return rest[2:]
    return rest if rest else None


def _parse_hunk(
    lines: list[str], start: int, hunk_match: re.Match
) -> tuple[DiffHunk, int]:
    """Parse a single hunk starting at the @@ line."""
    old_start = int(hunk_match.group(1))
    old_count = int(hunk_match.group(2)) if hunk_match.group(2) is not None else 1
    new_start = int(hunk_match.group(3))
    new_count = int(hunk_match.group(4)) if hunk_match.group(4) is not None else 1

    hunk = DiffHunk(
        old_start=old_start,
        old_count=old_count,
        new_start=new_start,
        new_count=new_count,
    )

    i = start + 1
    old_line = old_start
    new_line = new_start

    while i < len(lines):
        line = lines[i]

        # Stop at next hunk, next file, or end-of-diff markers
        if (
            _HUNK_HEADER_RE.match(line)
            or line.startswith("diff --git ")
            or line.startswith("--- ")
        ):
            break

        if line.startswith("+"):
            hunk.lines.append(
                DiffLine(
                    type="added",
                    content=line[1:],
                    old_line=None,
                    new_line=new_line,
                )
            )
            new_line += 1
        elif line.startswith("-"):
            hunk.lines.append(
                DiffLine(
                    type="removed",
                    content=line[1:],
                    old_line=old_line,
                    new_line=None,
                )
            )
            old_line += 1
        elif line.startswith("\\"):
            # "\ No newline at end of file" — skip
            pass
        else:
            # Context line (may have a leading space)
            content = line[1:] if line.startswith(" ") else line
            hunk.lines.append(
                DiffLine(
                    type="context",
                    content=content,
                    old_line=old_line,
                    new_line=new_line,
                )
            )
            old_line += 1
            new_line += 1

        i += 1

    return hunk, i


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def extract_new_code(diff_files: list[DiffFile]) -> str:
    """Extract only the new/added code for rule analysis.

    Concatenates all added lines from all files, separated by newlines.
    This enables running the existing findings engine against only the
    new code in a diff.
    """
    all_added: list[str] = []
    for df in diff_files:
        if df.is_binary or df.is_rename_only:
            continue
        added = df.added_lines
        if added:
            all_added.extend(added)
    return "\n".join(all_added)


def is_line_in_diff(line_number: int, diff_file: DiffFile) -> bool:
    """Check if a line number falls within a changed hunk.

    The *line_number* refers to the new file's line numbering.
    Returns True if the line is within any hunk's range of changed
    (added) lines.
    """
    for hunk in diff_file.hunks:
        hunk_new_end = hunk.new_start + hunk.new_count
        if hunk.new_start <= line_number < hunk_new_end:
            # Check if this specific line is an added line
            for dl in hunk.lines:
                if dl.new_line == line_number and dl.type == "added":
                    return True
    return False


def get_hunk_context(line_number: int, diff_file: DiffFile) -> str:
    """Return the diff hunk text containing the given line number."""
    for hunk in diff_file.hunks:
        hunk_new_end = hunk.new_start + hunk.new_count
        if hunk.new_start <= line_number < hunk_new_end:
            parts: list[str] = []
            parts.append(
                f"@@ -{hunk.old_start},{hunk.old_count} "
                f"+{hunk.new_start},{hunk.new_count} @@"
            )
            for dl in hunk.lines:
                if dl.type == "added":
                    parts.append(f"+{dl.content}")
                elif dl.type == "removed":
                    parts.append(f"-{dl.content}")
                else:
                    parts.append(f" {dl.content}")
            return "\n".join(parts)
    return ""
