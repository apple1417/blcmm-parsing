# Borderlands Internal Metadata Patterns

- [Borderlands Internal Metadata Patterns](#borderlands-internal-metadata-patterns)
- [Parsing](#parsing)
  - [First Comment Extraction](#first-comment-extraction)
    - [Generic Comment Extraction](#generic-comment-extraction)
    - [Filtertool Comment Extraction](#filtertool-comment-extraction)
    - [BLCMM Comment Extraction](#blcmm-comment-extraction)
  - [Tag Detection](#tag-detection)
  - [Tag Intepretation](#tag-intepretation)
- [Tests](#tests)

BLIMP is a standard for storing metadata within mod files. BLIMP parsers can then extract this
metadata for use in their own programs. Broadly speaking, BLIMP consists of a set of `@` tags in the
first comment block of the mod.

```
@title My Mod
@author apple1417 
@version 1.1
@description Does moddy things.
```

BLIMP is not restricted to just BLCMM files, but implementing a conforming BLIMP parser will require
implementing proper BLCMM parsing too, so it can be considered an extension of the parsing described
in the root of this repo.

# Parsing

BLIMP parsing consists of three major steps:
1. First Comment Extraction - finding the first block of comments.
2. Tag Detection - finding all tags within that block.
3. Tag Intepretation - intepreting the found tags.

The first two steps are entirely case insensitive. The third step is recommended to be case 
preserving, however this is not required, BLIMP allows arbitrary tags not defined in this document,
which may handle case differently.

## First Comment Extraction
The first step is to extract the first comment block. This depends on the exact mod file format. Mod
format is worked out by checking the first line of if the file:
- If it starts with `<BLCM`, it's a BLCMM file. This check may be case sensitive in conforming BLIMP
  parsers, but it is not required to be (and is in fact the only check allow case sensitivity).
- If it starts with `#<`, it's a FilterTool file.
- Otherwise, it's a generic mod file.

Each mod format goes through a different process, but they all return a set of comment lines, in the
order they were encountered, which are to be used by the next step.

It is possible for comment extraction to fail, if a file is malformed or not a mod file at all. What
to do in this case is undefined - different BLIMP parsers may choose to extract empty comments,
abort handling the given file completely, or whatever else they please.

### Generic Comment Extraction
Generic mod file comment extraction is the simplest - it's just all the content before the first
command. This is defined as:
- For each line in the file in sequence:
  - Check if the line starts with `set`, `say`, or `exec`. Leading whitespace is allowed.
    - If it doesn't, it's a comment, add it to the extracted comment list exactly as is -
      whitespace must be preserved.
    - If it does, it's a command, end parsing, without extracting the line.

Parsing reaching the end of the file without finding any commands is considered undefined behaviour,
though it's suggested to take this as meaning the file isn't actually a mod file.

### Filtertool Comment Extraction
Filtertool files have a bit of structure to aid in parsing. Broadly speaking, it's all the content
in the first category before the first command or subcategory. There is also an exception if the
first subcategory is explicitly a description category, if this is the case, it instead extracts all
the content in that subcategory before the next command or subcategory.

During this section:
- A category header is defined as a line matching the regex pattern `#<(.*)>`, allowing leading
  and/or trailing whitespace.
- The category name is defined as the first matching group of the category header's pattern.
- A command is defined as a line which starts with `set`, `say`, or `exec`, allowing leading
  whitespace.

The exact sequence to extract comments is:
1. Skip past the first category header.
    - This should be the very first line, given that's how the file type is decided. It's considered
      undefined behaviour if this is not the case - e.g. if the header is malformed.
2. Iterate over all following lines (not including the first category header)
    - If the line is a command, end parsing, without extracting the line.
    - If the line contains another category header, check if the category name contains the string
      `description`.
      - If so, discard the existing comments, and continue. This may only happen once. Multiple
        nested `description` categories are allowed to exist, but conforming BLIMP parsers must only
         recurse into the first.
      - If not, end parsing.
    - Otherwise, add the line to the extracted comment list exactly as is - whitespace must be 
      preserved.

   Reaching the end of file without having ended parsing is considered undefined behavior.

### BLCMM Comment Extraction
BLCMM files finally have some proper structure, making extracting data easier. They follow the same
broad idea as filtertool files.

Start by preprocessing the BLCMM file and feeding it through an XML parser, as described in the root
of this repo. The handling of files which are unable to be converted to XML is considered undefined
behaviour.

Extracting comments follows a similar process to filtertool files.
1. Check the `v` attribute on the root `BLCMM` tag. If it is not `1`, it's considered undefined
   behavior.
2. Follow the XPath `/BLCMM/body/category`
    - If this doesn't return an XML node, it's considered undefined behavior.
3. Iterate through all child nodes.
    - If the node is a `category` tag, check if it has an attribute `name`, which contains the
      string `description`.
      - If so, discard the existing comments, and look for those in this child node's children. This
        may only happen once. Multiple nested `description` categories are allowed, but conforming
        BLIMP parsers must only recurse into the first.
      - If not, end parsing.
    - If node is a `comment` tag, add the tag contents to the extracted comment list exactly as is, 
      preserving whitespace, *and* make sure to add a line seperator if the implementation requires
      one (since the comment contents won't have one naturally).
      implementation stores comments
    - Otherwise, end parsing.

   Running out of child nodes without having ended parsing is considered undefined behavior.

## Tag Detection
The result of first comment extraction is a set of comment lines. Tag detection then finds all tags 
contained within these lines, and their values. This is a quite simple process.

For each comment line:
1. Strip any trailing newlines. 
2. Check if the very first character (including whitespace) is a `@`.
    - If so, it's a tagged line. Look for the first space character.
      - If the space is immediately after the `@`, it's a malformed tag, ignore it.
      - If there is no space, the tag consists of the entirety of the line, with an empty string
        for it's value. Add this to the list of tags.
      - Otherwise, the tag consists of everything left of the space, while the value consists of
        everything to the right of the space (including extra whitespace). Add this to the list of
        tags.

      Multiples of the same tag are allowed, even with the same value, and must all be added in the
      order they were encontered. These will be stripped in the next step, if applicable.

    - Otherwise, ignore the line, or optionally add it to a list of untagged lines

Note that while this process preseves the order of values when multiple of the same tags are used,
it does not need to preseve the order of differing tags.

Conforming BLIMP parsers may, but are not required to, attempt to extract extra metadata from
untagged lines. This is mostly undefined, though there are two simple rules:
- If a comment line ever starts with a `@`, even if it's a malformed or unrecognised tag, it must
  never be used to extract metadata.
- Tags which were extracted normally must never be overwritten by, or have information appended
  from, data extracted from untagged lines.

## Tag Intepretation
Tag detection outputs a mapping of tag names to a list of the values those tags had. Arbitrary tag
names are allowed, and may be intepreted arbitrarily if the BLIMP parser recognises them. However,
this section defines a set of standard tags, and how they must be intepreted. BLIMP parsers are not
required to recognise all of the standard tags, but any they do must be intepreted as defined.

All standard tags strip leading/trailing whitespace in tag values.

Tag Name |  Multiple | Intepretation
:---|:---:|:---
`@author` | Allowed | The mod's author(s). Multiple authors can be joined in an implementation defined manner. If needed, the first `@author` tag is defined as the "main author".
`@categories` | Allowed | A list of comma and/or whitespace-separated categories for the mod. Multiple tags are all joined together into a single list of categories.
`@contact` | Allowed | Contact details for the mod's author(s).
`@description` | Allowed | Joined in the order encountered to create the mod's description. A tag with an empty value (after stripping whitespace) joins surrounding values with a newline, all other pairs are joined using a space.
`@homepage` | First | The primary mod homepage.
`@license` | First | The mod's licence's name.
`@license-url` | First | A url to the mod's license.
`@main-author` | First | Used as the mod's "main author", in place of the first `@author` tag.
`@screenshot` | Allowed | A url to a screenshot relevant to the mod. Labels can be added by prefixing the url with some text and a pipe `\|` separator.
`@title` | First | The mod's title.
`@version` | First | The mod's version. Entirely visual, should not be used to enforce version requirements.
`@video` | First | A url to a video relevant to the mod.

The multiple column defines which tag is used when multiple are present - either multiple tags are
allowed in general, or it picks a specific one and ignores all others.

# Tests
As with the regular BLCMM parsing, this repo also has a few test cases for BLIMP parsers, which can
be run using pytest and the `--program` arg.

```
pytest blimp/tests --program "my_blimp_parser"
```

As before, your test program should take a file on stdin, output to stdout, and exit with code 0.
The test program must stop after tag detection, it must not try to further process any tags it
recognises, and it must not include data extracted from untagged lines. The output should simply be
a json mapping of extracted tags and values.

```json
{
    "@tagname": [
        "first encountered value",
        "second encountered value",
    ]
}
```

Tag names may be output in any case, but tag values must be case preserving.
