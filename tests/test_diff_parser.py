"""Tests for the unified diff parser."""

from __future__ import annotations

import pytest

from app.engines.diff_parser import (
    DiffFile,
    DiffHunk,
    DiffLine,
    extract_new_code,
    get_hunk_context,
    is_line_in_diff,
    parse_unified_diff,
)


# ---------------------------------------------------------------------------
# Sample diffs
# ---------------------------------------------------------------------------

SIMPLE_DIFF = """\
diff --git a/src/zcl_order.clas.abap b/src/zcl_order.clas.abap
index abc1234..def5678 100644
--- a/src/zcl_order.clas.abap
+++ b/src/zcl_order.clas.abap
@@ -10,6 +10,8 @@ CLASS zcl_order IMPLEMENTATION.
   METHOD get_data.
     SELECT * FROM ztable INTO TABLE @rt_data.
+    " Added validation
+    CHECK rt_data IS NOT INITIAL.
     SORT rt_data BY order_id.
   ENDMETHOD.
 ENDCLASS.
"""

MULTI_FILE_DIFF = """\
diff --git a/src/zi_order.ddls.asddls b/src/zi_order.ddls.asddls
index 1111111..2222222 100644
--- a/src/zi_order.ddls.asddls
+++ b/src/zi_order.ddls.asddls
@@ -1,4 +1,5 @@
 define view entity ZI_ORDER as select from ztable {
   key order_id,
+      customer_name,
       status
 }
diff --git a/src/zcl_order.clas.abap b/src/zcl_order.clas.abap
index abc1234..def5678 100644
--- a/src/zcl_order.clas.abap
+++ b/src/zcl_order.clas.abap
@@ -5,3 +5,5 @@ CLASS zcl_order IMPLEMENTATION.
   METHOD get_data.
     SELECT * FROM ztable INTO TABLE @rt_data.
+    " New logic
+    LOOP AT rt_data ASSIGNING FIELD-SYMBOL(<fs>).
   ENDMETHOD.
"""

BINARY_DIFF = """\
diff --git a/images/logo.png b/images/logo.png
index 0000000..1111111 100644
Binary files /dev/null and b/images/logo.png differ
"""

RENAME_ONLY_DIFF = """\
diff --git a/src/old_name.abap b/src/new_name.abap
similarity index 100%
rename from src/old_name.abap
rename to src/new_name.abap
"""

NEW_FILE_DIFF = """\
diff --git a/src/zcl_new.clas.abap b/src/zcl_new.clas.abap
new file mode 100644
index 0000000..abc1234
--- /dev/null
+++ b/src/zcl_new.clas.abap
@@ -0,0 +1,5 @@
+CLASS zcl_new DEFINITION PUBLIC.
+  PUBLIC SECTION.
+    METHODS do_something.
+ENDCLASS.
+
"""

DELETION_DIFF = """\
diff --git a/src/zcl_old.clas.abap b/src/zcl_old.clas.abap
deleted file mode 100644
index abc1234..0000000
--- a/src/zcl_old.clas.abap
+++ /dev/null
@@ -1,3 +0,0 @@
-CLASS zcl_old DEFINITION PUBLIC.
-  PUBLIC SECTION.
-ENDCLASS.
"""

PLAIN_UNIFIED_DIFF = """\
--- a/file.abap
+++ b/file.abap
@@ -1,3 +1,4 @@
 METHOD test.
+  DATA lv_new TYPE string.
   DATA lv_old TYPE i.
 ENDMETHOD.
"""

MULTI_HUNK_DIFF = """\
diff --git a/src/zcl_test.clas.abap b/src/zcl_test.clas.abap
--- a/src/zcl_test.clas.abap
+++ b/src/zcl_test.clas.abap
@@ -1,4 +1,5 @@
 CLASS zcl_test DEFINITION PUBLIC.
+  " Added comment
   PUBLIC SECTION.
     METHODS do_something.
 ENDCLASS.
@@ -10,3 +11,4 @@ CLASS zcl_test IMPLEMENTATION.
   METHOD do_something.
     " existing logic
+    " new logic
   ENDMETHOD.
"""


# ---------------------------------------------------------------------------
# Tests: parse_unified_diff — standard
# ---------------------------------------------------------------------------


class TestParseUnifiedDiff:
    """Test standard unified diff parsing."""

    def test_parse_simple_diff(self):
        files = parse_unified_diff(SIMPLE_DIFF)
        assert len(files) == 1
        assert files[0].new_path == "src/zcl_order.clas.abap"

    def test_simple_diff_has_one_hunk(self):
        files = parse_unified_diff(SIMPLE_DIFF)
        assert len(files[0].hunks) == 1

    def test_simple_diff_hunk_header(self):
        files = parse_unified_diff(SIMPLE_DIFF)
        hunk = files[0].hunks[0]
        assert hunk.old_start == 10
        assert hunk.old_count == 6
        assert hunk.new_start == 10
        assert hunk.new_count == 8

    def test_simple_diff_added_lines(self):
        files = parse_unified_diff(SIMPLE_DIFF)
        added = files[0].added_lines
        assert len(added) == 2
        assert '    " Added validation' in added[0]
        assert "CHECK rt_data IS NOT INITIAL." in added[1]

    def test_simple_diff_removed_lines_empty(self):
        files = parse_unified_diff(SIMPLE_DIFF)
        assert files[0].removed_lines == []

    def test_simple_diff_context_lines(self):
        files = parse_unified_diff(SIMPLE_DIFF)
        context_lines = [
            dl for dl in files[0].hunks[0].lines if dl.type == "context"
        ]
        assert len(context_lines) >= 3

    def test_line_numbers_for_added_lines(self):
        files = parse_unified_diff(SIMPLE_DIFF)
        added = [dl for dl in files[0].hunks[0].lines if dl.type == "added"]
        # First added line is at new_line 12 (after 2 context lines starting at 10)
        assert added[0].new_line == 12
        assert added[0].old_line is None

    def test_line_numbers_for_context_lines(self):
        files = parse_unified_diff(SIMPLE_DIFF)
        ctx = [dl for dl in files[0].hunks[0].lines if dl.type == "context"]
        # First context line should have both old and new line numbers
        assert ctx[0].old_line is not None
        assert ctx[0].new_line is not None


class TestParseMultiFileDiff:
    """Test multi-file diff parsing."""

    def test_multi_file_count(self):
        files = parse_unified_diff(MULTI_FILE_DIFF)
        assert len(files) == 2

    def test_multi_file_paths(self):
        files = parse_unified_diff(MULTI_FILE_DIFF)
        assert files[0].new_path == "src/zi_order.ddls.asddls"
        assert files[1].new_path == "src/zcl_order.clas.abap"

    def test_multi_file_first_added(self):
        files = parse_unified_diff(MULTI_FILE_DIFF)
        assert len(files[0].added_lines) == 1
        assert "customer_name" in files[0].added_lines[0]

    def test_multi_file_second_added(self):
        files = parse_unified_diff(MULTI_FILE_DIFF)
        assert len(files[1].added_lines) == 2

    def test_multi_file_hunks(self):
        files = parse_unified_diff(MULTI_FILE_DIFF)
        assert len(files[0].hunks) == 1
        assert len(files[1].hunks) == 1


class TestBinaryAndSpecialDiffs:
    """Test edge cases: binary, rename, empty."""

    def test_binary_file(self):
        files = parse_unified_diff(BINARY_DIFF)
        assert len(files) == 1
        assert files[0].is_binary is True
        assert files[0].added_lines == []

    def test_rename_only(self):
        files = parse_unified_diff(RENAME_ONLY_DIFF)
        assert len(files) == 1
        assert files[0].is_rename_only is True
        assert files[0].hunks == []

    def test_empty_diff(self):
        files = parse_unified_diff("")
        assert files == []

    def test_whitespace_only_diff(self):
        files = parse_unified_diff("   \n  \n  ")
        assert files == []

    def test_new_file_diff(self):
        files = parse_unified_diff(NEW_FILE_DIFF)
        assert len(files) == 1
        assert len(files[0].added_lines) == 5

    def test_deletion_diff(self):
        files = parse_unified_diff(DELETION_DIFF)
        assert len(files) == 1
        assert len(files[0].removed_lines) == 3
        assert files[0].added_lines == []


class TestPlainUnifiedDiff:
    """Test plain unified diff without git header."""

    def test_plain_diff_parses(self):
        files = parse_unified_diff(PLAIN_UNIFIED_DIFF)
        assert len(files) == 1

    def test_plain_diff_added(self):
        files = parse_unified_diff(PLAIN_UNIFIED_DIFF)
        assert len(files[0].added_lines) == 1
        assert "lv_new" in files[0].added_lines[0]


class TestMultiHunkDiff:
    """Test diff with multiple hunks in a single file."""

    def test_multi_hunk_count(self):
        files = parse_unified_diff(MULTI_HUNK_DIFF)
        assert len(files) == 1
        assert len(files[0].hunks) == 2

    def test_multi_hunk_first(self):
        files = parse_unified_diff(MULTI_HUNK_DIFF)
        assert files[0].hunks[0].new_start == 1
        assert any("Added comment" in dl.content for dl in files[0].hunks[0].lines if dl.type == "added")

    def test_multi_hunk_second(self):
        files = parse_unified_diff(MULTI_HUNK_DIFF)
        assert files[0].hunks[1].new_start == 11
        assert any("new logic" in dl.content for dl in files[0].hunks[1].lines if dl.type == "added")


# ---------------------------------------------------------------------------
# Tests: extract_new_code
# ---------------------------------------------------------------------------


class TestExtractNewCode:
    """Test extracting new code from diffs."""

    def test_extract_from_simple(self):
        files = parse_unified_diff(SIMPLE_DIFF)
        code = extract_new_code(files)
        assert "Added validation" in code
        assert "CHECK rt_data IS NOT INITIAL" in code

    def test_extract_from_multi_file(self):
        files = parse_unified_diff(MULTI_FILE_DIFF)
        code = extract_new_code(files)
        assert "customer_name" in code
        assert "New logic" in code

    def test_extract_skips_binary(self):
        files = parse_unified_diff(BINARY_DIFF)
        code = extract_new_code(files)
        assert code == ""

    def test_extract_skips_rename(self):
        files = parse_unified_diff(RENAME_ONLY_DIFF)
        code = extract_new_code(files)
        assert code == ""

    def test_extract_from_empty(self):
        code = extract_new_code([])
        assert code == ""

    def test_extract_new_file(self):
        files = parse_unified_diff(NEW_FILE_DIFF)
        code = extract_new_code(files)
        assert "CLASS zcl_new DEFINITION PUBLIC" in code


# ---------------------------------------------------------------------------
# Tests: is_line_in_diff
# ---------------------------------------------------------------------------


class TestIsLineInDiff:
    """Test line-in-diff checking."""

    def test_added_line_is_in_diff(self):
        files = parse_unified_diff(SIMPLE_DIFF)
        # Line 12 is first added line
        assert is_line_in_diff(12, files[0]) is True

    def test_context_line_not_in_diff(self):
        files = parse_unified_diff(SIMPLE_DIFF)
        # Line 10 is context
        assert is_line_in_diff(10, files[0]) is False

    def test_line_outside_hunk_not_in_diff(self):
        files = parse_unified_diff(SIMPLE_DIFF)
        assert is_line_in_diff(1, files[0]) is False

    def test_line_in_second_hunk(self):
        files = parse_unified_diff(MULTI_HUNK_DIFF)
        # Second hunk starts at new_start=11
        added = [dl for dl in files[0].hunks[1].lines if dl.type == "added"]
        if added:
            assert is_line_in_diff(added[0].new_line, files[0]) is True

    def test_removed_line_not_marked_as_in_diff(self):
        files = parse_unified_diff(DELETION_DIFF)
        # Removed lines are from old file, not new
        assert is_line_in_diff(1, files[0]) is False


# ---------------------------------------------------------------------------
# Tests: get_hunk_context
# ---------------------------------------------------------------------------


class TestGetHunkContext:
    """Test hunk context extraction."""

    def test_context_for_added_line(self):
        files = parse_unified_diff(SIMPLE_DIFF)
        ctx = get_hunk_context(12, files[0])
        assert "@@" in ctx
        assert "+" in ctx

    def test_context_for_line_outside(self):
        files = parse_unified_diff(SIMPLE_DIFF)
        ctx = get_hunk_context(1, files[0])
        assert ctx == ""
