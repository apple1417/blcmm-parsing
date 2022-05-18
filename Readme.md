# BLCMM Parsing
While BLCMM files look like XML with a few things appended, for some inexplicable reason they use
completely custom escaping logic. This requires either writing a completely new parser, or more
reasonably, just adding an additional step to convert them to valid XML anyway. This repo contains a
reference C++ preprocessor, as well as a series of test cases and a Python test script to run them.

## Format Rules
The main format differences between BLCMM files and XML can be summaried in the following rules.

The handling of any situations which cause BLCMM to fail loading a file is considered undefined
behaviour. Known causes are also listed below.

- The filtertool warning should be removed, or converted to an XML comment. The warning is always on
  it's own line (leading/trailing whitespace allowed), and is always the exact string:
  ```
  #<!!!You opened a file saved with BLCMM in FilterTool. Please update to BLCMM to properly open this file!!!>
  ```
- Attribute values are always surrounded with double quotes. The only escape sequence is `\"`,
  evaluating to a double quote. Backslashes elsewhere are just interpreted literally; a value ending
  with a backslash is considered undefined behaviour.
- Nested elements always have the opening outer tag on one line, each inner tag on its own line,
  and the closing outer tag on another. Whitespace between inner tags is ignored.
- Tags with text content are always entirely on a single line, and interpret all characters between
  the opening tag and closing tag literally. Other tags are allowed to appear within this range,
  with a few exceptions:
  - If the text content contains an "inner tag" of the same type (e.g. the string `<comment>` in the
    text content of a `comment` tag), it's considered undefined behaviour. This applies to any
    presense of the tag at all, regardless of opening/closing, whitespace, or attributes.
  - If an "inner tag" has spaces between the tag name or last attribute and the closing `>` or `/>`,
    it's considered undefined behaviour. Other whitespace, or no spaces at all, is allowed.
  Additionally, a few specific tags have extra format rules:
  - `code` tags' text must always start with the exact string `set ` (including the space). If the
    parent tag is a `hotfix`, `set_cmp` (no space needed) is also an acceptable start. In either
    case, the text must also contain at least two whitespace-seperated "words" (just groups of
    non-whitespace characters) after the starting string. Any of these rules being broken results in
    undefined behaviour.
- After the closing root tag, the file contains arbitrary commands, which should all be removed or
  converted into XML comments.

The test cases follow these rules too - i.e. you will never be given a file with the filtertool
warning split across two lines, but as tags aren't specified you may be given a file which doesn't
use the standard BLCMM ones.

## Using the Tester
To use the tester, simply simply run `tester.py`, with a command to run your test program as the
first argument. Your test program should take a BLCMM file as stdin, output equivalent XML to
stdout, and then exit with code 0. A non-zero exit code will be considered a crash. There is a
default timeout of 10s, which will also cause a failure, use the `--timeout` argument to overwrite
it if needed. Stderr is not touched, and should still be piped through to your terminal, to print
any exceptions or if you need debug logging. There are no rules to the formatting of the outputted
XML (outside of it must be valid), it will be canonicalized (with XML comments stripped) before
being compared.

### Test Cases
The test cases can be split into three categories.

Category     | Contents
:------------|:---------
`standard`   | Regular BLCMM files created entirely within the program, which can successfully be loaded and don't change on re-save.
`edited`     | Files which were manually edited, but which still successfully load and re-save without change.
`formatting` | Files which follow the formatting rules above, but can't be loaded by BLCMM, can be loaded but change on re-save, or just plain aren't BLCMM files.

You can use the `--categories` argument to select which categories to run - it defaults to all.
