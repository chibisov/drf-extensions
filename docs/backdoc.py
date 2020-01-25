#!/usr/bin/env python
"""
Backdoc is a tool for backbone-like documentation generation. 
Backdoc main goal is to help to generate one page documentation from one markdown source file.

https://github.com/chibisov/backdoc
"""
import sys
import argparse

# Copyright (c) 2012 Trent Mick.
# Copyright (c) 2007-2008 ActiveState Corp.
# License: MIT (http://www.opensource.org/licenses/mit-license.php)

r"""A fast and complete Python implementation of Markdown.

[from http://daringfireball.net/projects/markdown/]
> Markdown is a text-to-HTML filter; it translates an easy-to-read /
> easy-to-write structured text format into HTML.  Markdown's text
> format is most similar to that of plain text email, and supports
> features such as headers, *emphasis*, code blocks, blockquotes, and
> links.
>
> Markdown's syntax is designed not as a generic markup language, but
> specifically to serve as a front-end to (X)HTML. You can use span-level
> HTML tags anywhere in a Markdown document, and you can use block level
> HTML tags (like <div> and <table> as well).

Module usage:

    >>> import markdown2
    >>> markdown2.markdown("*boo!*")  # or use `html = markdown_path(PATH)`
    u'<p><em>boo!</em></p>\n'

    >>> markdowner = Markdown()
    >>> markdowner.convert("*boo!*")
    u'<p><em>boo!</em></p>\n'
    >>> markdowner.convert("**boom!**")
    u'<p><strong>boom!</strong></p>\n'

This implementation of Markdown implements the full "core" syntax plus a
number of extras (e.g., code syntax coloring, footnotes) as described on
<https://github.com/trentm/python-markdown2/wiki/Extras>.
"""

cmdln_desc = """A fast and complete Python implementation of Markdown, a
text-to-HTML conversion tool for web writers.

Supported extra syntax options (see -x|--extras option below and
see <https://github.com/trentm/python-markdown2/wiki/Extras> for details):

* code-friendly: Disable _ and __ for em and strong.
* cuddled-lists: Allow lists to be cuddled to the preceding paragraph.
* fenced-code-blocks: Allows a code block to not have to be indented
  by fencing it with '```' on a line before and after. Based on
  <http://github.github.com/github-flavored-markdown/> with support for
  syntax highlighting.
* footnotes: Support footnotes as in use on daringfireball.net and
  implemented in other Markdown processors (tho not in Markdown.pl v1.0.1).
* header-ids: Adds "id" attributes to headers. The id value is a slug of
  the header text.
* html-classes: Takes a dict mapping html tag names (lowercase) to a
  string to use for a "class" tag attribute. Currently only supports
  "pre" and "code" tags. Add an issue if you require this for other tags.
* markdown-in-html: Allow the use of `markdown="1"` in a block HTML tag to
  have markdown processing be done on its contents. Similar to
  <http://michelf.com/projects/php-markdown/extra/#markdown-attr> but with
  some limitations.
* metadata: Extract metadata from a leading '---'-fenced block.
  See <https://github.com/trentm/python-markdown2/issues/77> for details.
* nofollow: Add `rel="nofollow"` to add `<a>` tags with an href. See
  <http://en.wikipedia.org/wiki/Nofollow>.
* pyshell: Treats unindented Python interactive shell sessions as <code>
  blocks.
* link-patterns: Auto-link given regex patterns in text (e.g. bug number
  references, revision number references).
* smarty-pants: Replaces ' and " with curly quotation marks or curly
  apostrophes.  Replaces --, ---, ..., and . . . with en dashes, em dashes,
  and ellipses.
* toc: The returned HTML string gets a new "toc_html" attribute which is
  a Table of Contents for the document. (experimental)
* xml: Passes one-liner processing instructions and namespaced XML tags.
* wiki-tables: Google Code Wiki-style tables. See
  <http://code.google.com/p/support/wiki/WikiSyntax#Tables>.
"""

# Dev Notes:
# - Python's regex syntax doesn't have '\z', so I'm using '\Z'. I'm
#   not yet sure if there implications with this. Compare 'pydoc sre'
#   and 'perldoc perlre'.

__version_info__ = (2, 1, 1)
__version__ = '.'.join(map(str, __version_info__))
__author__ = "Trent Mick"

import os
import sys
from pprint import pprint
import re
import logging
try:
    from hashlib import md5
except ImportError:
    from md5 import md5
import optparse
from random import random, randint
import codecs


#---- Python version compat

try:
    from urllib.parse import quote # python3
except ImportError:
    from urllib import quote # python2

if sys.version_info[:2] < (2,4):
    from sets import Set as set
    def reversed(sequence):
        for i in sequence[::-1]:
            yield i

# Use `bytes` for byte strings and `unicode` for unicode strings (str in Py3).
if sys.version_info[0] <= 2:
    py3 = False
    try:
        bytes
    except NameError:
        bytes = str
    base_string_type = basestring
elif sys.version_info[0] >= 3:
    py3 = True
    unicode = str
    base_string_type = str



#---- globals

DEBUG = False
log = logging.getLogger("markdown")

DEFAULT_TAB_WIDTH = 4


SECRET_SALT = bytes(randint(0, 1000000))
def _hash_text(s):
    return 'md5-' + md5(SECRET_SALT + s.encode("utf-8")).hexdigest()

# Table of hash values for escaped characters:
g_escape_table = dict([(ch, _hash_text(ch))
    for ch in '\\`*_{}[]()>#+-.!'])



#---- exceptions

class MarkdownError(Exception):
    pass



#---- public api

def markdown_path(path, encoding="utf-8",
                  html4tags=False, tab_width=DEFAULT_TAB_WIDTH,
                  safe_mode=None, extras=None, link_patterns=None,
                  use_file_vars=False):
    fp = codecs.open(path, 'r', encoding)
    text = fp.read()
    fp.close()
    return Markdown(html4tags=html4tags, tab_width=tab_width,
                    safe_mode=safe_mode, extras=extras,
                    link_patterns=link_patterns,
                    use_file_vars=use_file_vars).convert(text)

def markdown(text, html4tags=False, tab_width=DEFAULT_TAB_WIDTH,
             safe_mode=None, extras=None, link_patterns=None,
             use_file_vars=False):
    return Markdown(html4tags=html4tags, tab_width=tab_width,
                    safe_mode=safe_mode, extras=extras,
                    link_patterns=link_patterns,
                    use_file_vars=use_file_vars).convert(text)

class Markdown:
    # The dict of "extras" to enable in processing -- a mapping of
    # extra name to argument for the extra. Most extras do not have an
    # argument, in which case the value is None.
    #
    # This can be set via (a) subclassing and (b) the constructor
    # "extras" argument.
    extras = None

    urls = None
    titles = None
    html_blocks = None
    html_spans = None
    html_removed_text = "[HTML_REMOVED]"  # for compat with markdown.py

    # Used to track when we're inside an ordered or unordered list
    # (see _ProcessListItems() for details):
    list_level = 0

    _ws_only_line_re = re.compile(r"^[ \t]+$", re.M)

    def __init__(self, html4tags=False, tab_width=4, safe_mode=None,
                 extras=None, link_patterns=None, use_file_vars=False):
        if html4tags:
            self.empty_element_suffix = ">"
        else:
            self.empty_element_suffix = " />"
        self.tab_width = tab_width

        # For compatibility with earlier markdown2.py and with
        # markdown.py's safe_mode being a boolean,
        #   safe_mode == True -> "replace"
        if safe_mode is True:
            self.safe_mode = "replace"
        else:
            self.safe_mode = safe_mode

        # Massaging and building the "extras" info.
        if self.extras is None:
            self.extras = {}
        elif not isinstance(self.extras, dict):
            self.extras = dict([(e, None) for e in self.extras])
        if extras:
            if not isinstance(extras, dict):
                extras = dict([(e, None) for e in extras])
            self.extras.update(extras)
        assert isinstance(self.extras, dict)
        if "toc" in self.extras and not "header-ids" in self.extras:
            self.extras["header-ids"] = None   # "toc" implies "header-ids"
        self._instance_extras = self.extras.copy()

        self.link_patterns = link_patterns
        self.use_file_vars = use_file_vars
        self._outdent_re = re.compile(r'^(\t|[ ]{1,%d})' % tab_width, re.M)

        self._escape_table = g_escape_table.copy()
        if "smarty-pants" in self.extras:
            self._escape_table['"'] = _hash_text('"')
            self._escape_table["'"] = _hash_text("'")

    def reset(self):
        self.urls = {}
        self.titles = {}
        self.html_blocks = {}
        self.html_spans = {}
        self.list_level = 0
        self.extras = self._instance_extras.copy()
        if "footnotes" in self.extras:
            self.footnotes = {}
            self.footnote_ids = []
        if "header-ids" in self.extras:
            self._count_from_header_id = {} # no `defaultdict` in Python 2.4
        if "metadata" in self.extras:
            self.metadata = {}

    # Per <https://developer.mozilla.org/en-US/docs/HTML/Element/a> "rel"
    # should only be used in <a> tags with an "href" attribute.
    _a_nofollow = re.compile(r"<(a)([^>]*href=)", re.IGNORECASE)

    def convert(self, text):
        """Convert the given text."""
        # Main function. The order in which other subs are called here is
        # essential. Link and image substitutions need to happen before
        # _EscapeSpecialChars(), so that any *'s or _'s in the <a>
        # and <img> tags get encoded.

        # Clear the global hashes. If we don't clear these, you get conflicts
        # from other articles when generating a page which contains more than
        # one article (e.g. an index page that shows the N most recent
        # articles):
        self.reset()

        if not isinstance(text, unicode):
            #TODO: perhaps shouldn't presume UTF-8 for string input?
            text = unicode(text, 'utf-8')

        if self.use_file_vars:
            # Look for emacs-style file variable hints.
            emacs_vars = self._get_emacs_vars(text)
            if "markdown-extras" in emacs_vars:
                splitter = re.compile("[ ,]+")
                for e in splitter.split(emacs_vars["markdown-extras"]):
                    if '=' in e:
                        ename, earg = e.split('=', 1)
                        try:
                            earg = int(earg)
                        except ValueError:
                            pass
                    else:
                        ename, earg = e, None
                    self.extras[ename] = earg

        # Standardize line endings:
        text = re.sub("\r\n|\r", "\n", text)

        # Make sure $text ends with a couple of newlines:
        text += "\n\n"

        # Convert all tabs to spaces.
        text = self._detab(text)

        # Strip any lines consisting only of spaces and tabs.
        # This makes subsequent regexen easier to write, because we can
        # match consecutive blank lines with /\n+/ instead of something
        # contorted like /[ \t]*\n+/ .
        text = self._ws_only_line_re.sub("", text)

        # strip metadata from head and extract
        if "metadata" in self.extras:
            text = self._extract_metadata(text)

        text = self.preprocess(text)

        if self.safe_mode:
            text = self._hash_html_spans(text)

        # Turn block-level HTML blocks into hash entries
        text = self._hash_html_blocks(text, raw=True)

        # Strip link definitions, store in hashes.
        if "footnotes" in self.extras:
            # Must do footnotes first because an unlucky footnote defn
            # looks like a link defn:
            #   [^4]: this "looks like a link defn"
            text = self._strip_footnote_definitions(text)
        text = self._strip_link_definitions(text)

        text = self._run_block_gamut(text)

        if "footnotes" in self.extras:
            text = self._add_footnotes(text)

        text = self.postprocess(text)

        text = self._unescape_special_chars(text)

        if self.safe_mode:
            text = self._unhash_html_spans(text)

        if "nofollow" in self.extras:
            text = self._a_nofollow.sub(r'<\1 rel="nofollow"\2', text)

        text += "\n"

        rv = UnicodeWithAttrs(text)
        if "toc" in self.extras:
            rv._toc = self._toc
        if "metadata" in self.extras:
            rv.metadata = self.metadata
        return rv

    def postprocess(self, text):
        """A hook for subclasses to do some postprocessing of the html, if
        desired. This is called before unescaping of special chars and
        unhashing of raw HTML spans.
        """
        return text

    def preprocess(self, text):
        """A hook for subclasses to do some preprocessing of the Markdown, if
        desired. This is called after basic formatting of the text, but prior
        to any extras, safe mode, etc. processing.
        """
        return text

    # Is metadata if the content starts with '---'-fenced `key: value`
    # pairs. E.g. (indented for presentation):
    #   ---
    #   foo: bar
    #   another-var: blah blah
    #   ---
    _metadata_pat = re.compile("""^---[ \t]*\n((?:[ \t]*[^ \t:]+[ \t]*:[^\n]*\n)+)---[ \t]*\n""")

    def _extract_metadata(self, text):
        # fast test
        if not text.startswith("---"):
            return text
        match = self._metadata_pat.match(text)
        if not match:
            return text

        tail = text[len(match.group(0)):]
        metadata_str = match.group(1).strip()
        for line in metadata_str.split('\n'):
            key, value = line.split(':', 1)
            self.metadata[key.strip()] = value.strip()

        return tail


    _emacs_oneliner_vars_pat = re.compile(r"-\*-\s*([^\r\n]*?)\s*-\*-", re.UNICODE)
    # This regular expression is intended to match blocks like this:
    #    PREFIX Local Variables: SUFFIX
    #    PREFIX mode: Tcl SUFFIX
    #    PREFIX End: SUFFIX
    # Some notes:
    # - "[ \t]" is used instead of "\s" to specifically exclude newlines
    # - "(\r\n|\n|\r)" is used instead of "$" because the sre engine does
    #   not like anything other than Unix-style line terminators.
    _emacs_local_vars_pat = re.compile(r"""^
        (?P<prefix>(?:[^\r\n|\n|\r])*?)
        [\ \t]*Local\ Variables:[\ \t]*
        (?P<suffix>.*?)(?:\r\n|\n|\r)
        (?P<content>.*?\1End:)
        """, re.IGNORECASE | re.MULTILINE | re.DOTALL | re.VERBOSE)

    def _get_emacs_vars(self, text):
        """Return a dictionary of emacs-style local variables.

        Parsing is done loosely according to this spec (and according to
        some in-practice deviations from this):
        http://www.gnu.org/software/emacs/manual/html_node/emacs/Specifying-File-Variables.html#Specifying-File-Variables
        """
        emacs_vars = {}
        SIZE = pow(2, 13) # 8kB

        # Search near the start for a '-*-'-style one-liner of variables.
        head = text[:SIZE]
        if "-*-" in head:
            match = self._emacs_oneliner_vars_pat.search(head)
            if match:
                emacs_vars_str = match.group(1)
                assert '\n' not in emacs_vars_str
                emacs_var_strs = [s.strip() for s in emacs_vars_str.split(';')
                                  if s.strip()]
                if len(emacs_var_strs) == 1 and ':' not in emacs_var_strs[0]:
                    # While not in the spec, this form is allowed by emacs:
                    #   -*- Tcl -*-
                    # where the implied "variable" is "mode". This form
                    # is only allowed if there are no other variables.
                    emacs_vars["mode"] = emacs_var_strs[0].strip()
                else:
                    for emacs_var_str in emacs_var_strs:
                        try:
                            variable, value = emacs_var_str.strip().split(':', 1)
                        except ValueError:
                            log.debug("emacs variables error: malformed -*- "
                                      "line: %r", emacs_var_str)
                            continue
                        # Lowercase the variable name because Emacs allows "Mode"
                        # or "mode" or "MoDe", etc.
                        emacs_vars[variable.lower()] = value.strip()

        tail = text[-SIZE:]
        if "Local Variables" in tail:
            match = self._emacs_local_vars_pat.search(tail)
            if match:
                prefix = match.group("prefix")
                suffix = match.group("suffix")
                lines = match.group("content").splitlines(0)
                #print "prefix=%r, suffix=%r, content=%r, lines: %s"\
                #      % (prefix, suffix, match.group("content"), lines)

                # Validate the Local Variables block: proper prefix and suffix
                # usage.
                for i, line in enumerate(lines):
                    if not line.startswith(prefix):
                        log.debug("emacs variables error: line '%s' "
                                  "does not use proper prefix '%s'"
                                  % (line, prefix))
                        return {}
                    # Don't validate suffix on last line. Emacs doesn't care,
                    # neither should we.
                    if i != len(lines)-1 and not line.endswith(suffix):
                        log.debug("emacs variables error: line '%s' "
                                  "does not use proper suffix '%s'"
                                  % (line, suffix))
                        return {}

                # Parse out one emacs var per line.
                continued_for = None
                for line in lines[:-1]: # no var on the last line ("PREFIX End:")
                    if prefix: line = line[len(prefix):] # strip prefix
                    if suffix: line = line[:-len(suffix)] # strip suffix
                    line = line.strip()
                    if continued_for:
                        variable = continued_for
                        if line.endswith('\\'):
                            line = line[:-1].rstrip()
                        else:
                            continued_for = None
                        emacs_vars[variable] += ' ' + line
                    else:
                        try:
                            variable, value = line.split(':', 1)
                        except ValueError:
                            log.debug("local variables error: missing colon "
                                      "in local variables entry: '%s'" % line)
                            continue
                        # Do NOT lowercase the variable name, because Emacs only
                        # allows "mode" (and not "Mode", "MoDe", etc.) in this block.
                        value = value.strip()
                        if value.endswith('\\'):
                            value = value[:-1].rstrip()
                            continued_for = variable
                        else:
                            continued_for = None
                        emacs_vars[variable] = value

        # Unquote values.
        for var, val in list(emacs_vars.items()):
            if len(val) > 1 and (val.startswith('"') and val.endswith('"')
               or val.startswith('"') and val.endswith('"')):
                emacs_vars[var] = val[1:-1]

        return emacs_vars

    # Cribbed from a post by Bart Lateur:
    # <http://www.nntp.perl.org/group/perl.macperl.anyperl/154>
    _detab_re = re.compile(r'(.*?)\t', re.M)
    def _detab_sub(self, match):
        g1 = match.group(1)
        return g1 + (' ' * (self.tab_width - len(g1) % self.tab_width))
    def _detab(self, text):
        r"""Remove (leading?) tabs from a file.

            >>> m = Markdown()
            >>> m._detab("\tfoo")
            '    foo'
            >>> m._detab("  \tfoo")
            '    foo'
            >>> m._detab("\t  foo")
            '      foo'
            >>> m._detab("  foo")
            '  foo'
            >>> m._detab("  foo\n\tbar\tblam")
            '  foo\n    bar blam'
        """
        if '\t' not in text:
            return text
        return self._detab_re.subn(self._detab_sub, text)[0]

    # I broke out the html5 tags here and add them to _block_tags_a and
    # _block_tags_b.  This way html5 tags are easy to keep track of.
    _html5tags = '|article|aside|header|hgroup|footer|nav|section|figure|figcaption'

    _block_tags_a = 'p|div|h[1-6]|blockquote|pre|table|dl|ol|ul|script|noscript|form|fieldset|iframe|math|ins|del'
    _block_tags_a += _html5tags

    _strict_tag_block_re = re.compile(r"""
        (                       # save in \1
            ^                   # start of line  (with re.M)
            <(%s)               # start tag = \2
            \b                  # word break
            (.*\n)*?            # any number of lines, minimally matching
            </\2>               # the matching end tag
            [ \t]*              # trailing spaces/tabs
            (?=\n+|\Z)          # followed by a newline or end of document
        )
        """ % _block_tags_a,
        re.X | re.M)

    _block_tags_b = 'p|div|h[1-6]|blockquote|pre|table|dl|ol|ul|script|noscript|form|fieldset|iframe|math'
    _block_tags_b += _html5tags

    _liberal_tag_block_re = re.compile(r"""
        (                       # save in \1
            ^                   # start of line  (with re.M)
            <(%s)               # start tag = \2
            \b                  # word break
            (.*\n)*?            # any number of lines, minimally matching
            .*</\2>             # the matching end tag
            [ \t]*              # trailing spaces/tabs
            (?=\n+|\Z)          # followed by a newline or end of document
        )
        """ % _block_tags_b,
        re.X | re.M)

    _html_markdown_attr_re = re.compile(
        r'''\s+markdown=("1"|'1')''')
    def _hash_html_block_sub(self, match, raw=False):
        html = match.group(1)
        if raw and self.safe_mode:
            html = self._sanitize_html(html)
        elif 'markdown-in-html' in self.extras and 'markdown=' in html:
            first_line = html.split('\n', 1)[0]
            m = self._html_markdown_attr_re.search(first_line)
            if m:
                lines = html.split('\n')
                middle = '\n'.join(lines[1:-1])
                last_line = lines[-1]
                first_line = first_line[:m.start()] + first_line[m.end():]
                f_key = _hash_text(first_line)
                self.html_blocks[f_key] = first_line
                l_key = _hash_text(last_line)
                self.html_blocks[l_key] = last_line
                return ''.join(["\n\n", f_key,
                    "\n\n", middle, "\n\n",
                    l_key, "\n\n"])
        key = _hash_text(html)
        self.html_blocks[key] = html
        return "\n\n" + key + "\n\n"

    def _hash_html_blocks(self, text, raw=False):
        """Hashify HTML blocks

        We only want to do this for block-level HTML tags, such as headers,
        lists, and tables. That's because we still want to wrap <p>s around
        "paragraphs" that are wrapped in non-block-level tags, such as anchors,
        phrase emphasis, and spans. The list of tags we're looking for is
        hard-coded.

        @param raw {boolean} indicates if these are raw HTML blocks in
            the original source. It makes a difference in "safe" mode.
        """
        if '<' not in text:
            return text

        # Pass `raw` value into our calls to self._hash_html_block_sub.
        hash_html_block_sub = _curry(self._hash_html_block_sub, raw=raw)

        # First, look for nested blocks, e.g.:
        #   <div>
        #       <div>
        #       tags for inner block must be indented.
        #       </div>
        #   </div>
        #
        # The outermost tags must start at the left margin for this to match, and
        # the inner nested divs must be indented.
        # We need to do this before the next, more liberal match, because the next
        # match will start at the first `<div>` and stop at the first `</div>`.
        text = self._strict_tag_block_re.sub(hash_html_block_sub, text)

        # Now match more liberally, simply from `\n<tag>` to `</tag>\n`
        text = self._liberal_tag_block_re.sub(hash_html_block_sub, text)

        # Special case just for <hr />. It was easier to make a special
        # case than to make the other regex more complicated.
        if "<hr" in text:
            _hr_tag_re = _hr_tag_re_from_tab_width(self.tab_width)
            text = _hr_tag_re.sub(hash_html_block_sub, text)

        # Special case for standalone HTML comments:
        if "<!--" in text:
            start = 0
            while True:
                # Delimiters for next comment block.
                try:
                    start_idx = text.index("<!--", start)
                except ValueError:
                    break
                try:
                    end_idx = text.index("-->", start_idx) + 3
                except ValueError:
                    break

                # Start position for next comment block search.
                start = end_idx

                # Validate whitespace before comment.
                if start_idx:
                    # - Up to `tab_width - 1` spaces before start_idx.
                    for i in range(self.tab_width - 1):
                        if text[start_idx - 1] != ' ':
                            break
                        start_idx -= 1
                        if start_idx == 0:
                            break
                    # - Must be preceded by 2 newlines or hit the start of
                    #   the document.
                    if start_idx == 0:
                        pass
                    elif start_idx == 1 and text[0] == '\n':
                        start_idx = 0  # to match minute detail of Markdown.pl regex
                    elif text[start_idx-2:start_idx] == '\n\n':
                        pass
                    else:
                        break

                # Validate whitespace after comment.
                # - Any number of spaces and tabs.
                while end_idx < len(text):
                    if text[end_idx] not in ' \t':
                        break
                    end_idx += 1
                # - Must be following by 2 newlines or hit end of text.
                if text[end_idx:end_idx+2] not in ('', '\n', '\n\n'):
                    continue

                # Escape and hash (must match `_hash_html_block_sub`).
                html = text[start_idx:end_idx]
                if raw and self.safe_mode:
                    html = self._sanitize_html(html)
                key = _hash_text(html)
                self.html_blocks[key] = html
                text = text[:start_idx] + "\n\n" + key + "\n\n" + text[end_idx:]

        if "xml" in self.extras:
            # Treat XML processing instructions and namespaced one-liner
            # tags as if they were block HTML tags. E.g., if standalone
            # (i.e. are their own paragraph), the following do not get
            # wrapped in a <p> tag:
            #    <?foo bar?>
            #
            #    <xi:include xmlns:xi="http://www.w3.org/2001/XInclude" href="chapter_1.md"/>
            _xml_oneliner_re = _xml_oneliner_re_from_tab_width(self.tab_width)
            text = _xml_oneliner_re.sub(hash_html_block_sub, text)

        return text

    def _strip_link_definitions(self, text):
        # Strips link definitions from text, stores the URLs and titles in
        # hash references.
        less_than_tab = self.tab_width - 1

        # Link defs are in the form:
        #   [id]: url "optional title"
        _link_def_re = re.compile(r"""
            ^[ ]{0,%d}\[(.+)\]: # id = \1
              [ \t]*
              \n?               # maybe *one* newline
              [ \t]*
            <?(.+?)>?           # url = \2
              [ \t]*
            (?:
                \n?             # maybe one newline
                [ \t]*
                (?<=\s)         # lookbehind for whitespace
                ['"(]
                ([^\n]*)        # title = \3
                ['")]
                [ \t]*
            )?  # title is optional
            (?:\n+|\Z)
            """ % less_than_tab, re.X | re.M | re.U)
        return _link_def_re.sub(self._extract_link_def_sub, text)

    def _extract_link_def_sub(self, match):
        id, url, title = match.groups()
        key = id.lower()    # Link IDs are case-insensitive
        self.urls[key] = self._encode_amps_and_angles(url)
        if title:
            self.titles[key] = title
        return ""

    def _extract_footnote_def_sub(self, match):
        id, text = match.groups()
        text = _dedent(text, skip_first_line=not text.startswith('\n')).strip()
        normed_id = re.sub(r'\W', '-', id)
        # Ensure footnote text ends with a couple newlines (for some
        # block gamut matches).
        self.footnotes[normed_id] = text + "\n\n"
        return ""

    def _strip_footnote_definitions(self, text):
        """A footnote definition looks like this:

            [^note-id]: Text of the note.

                May include one or more indented paragraphs.

        Where,
        - The 'note-id' can be pretty much anything, though typically it
          is the number of the footnote.
        - The first paragraph may start on the next line, like so:

            [^note-id]:
                Text of the note.
        """
        less_than_tab = self.tab_width - 1
        footnote_def_re = re.compile(r'''
            ^[ ]{0,%d}\[\^(.+)\]:   # id = \1
            [ \t]*
            (                       # footnote text = \2
              # First line need not start with the spaces.
              (?:\s*.*\n+)
              (?:
                (?:[ ]{%d} | \t)  # Subsequent lines must be indented.
                .*\n+
              )*
            )
            # Lookahead for non-space at line-start, or end of doc.
            (?:(?=^[ ]{0,%d}\S)|\Z)
            ''' % (less_than_tab, self.tab_width, self.tab_width),
            re.X | re.M)
        return footnote_def_re.sub(self._extract_footnote_def_sub, text)


    _hr_data = [
        ('*', re.compile(r"^[ ]{0,3}\*(.*?)$", re.M)),
        ('-', re.compile(r"^[ ]{0,3}\-(.*?)$", re.M)),
        ('_', re.compile(r"^[ ]{0,3}\_(.*?)$", re.M)),
    ]

    def _run_block_gamut(self, text):
        # These are all the transformations that form block-level
        # tags like paragraphs, headers, and list items.

        if "fenced-code-blocks" in self.extras:
            text = self._do_fenced_code_blocks(text)

        text = self._do_headers(text)

        # Do Horizontal Rules:
        # On the number of spaces in horizontal rules: The spec is fuzzy: "If
        # you wish, you may use spaces between the hyphens or asterisks."
        # Markdown.pl 1.0.1's hr regexes limit the number of spaces between the
        # hr chars to one or two. We'll reproduce that limit here.
        hr = "\n<hr"+self.empty_element_suffix+"\n"
        for ch, regex in self._hr_data:
            if ch in text:
                for m in reversed(list(regex.finditer(text))):
                    tail = m.group(1).rstrip()
                    if not tail.strip(ch + ' ') and tail.count("   ") == 0:
                        start, end = m.span()
                        text = text[:start] + hr + text[end:]

        text = self._do_lists(text)

        if "pyshell" in self.extras:
            text = self._prepare_pyshell_blocks(text)
        if "wiki-tables" in self.extras:
            text = self._do_wiki_tables(text)

        text = self._do_code_blocks(text)

        text = self._do_block_quotes(text)

        # We already ran _HashHTMLBlocks() before, in Markdown(), but that
        # was to escape raw HTML in the original Markdown source. This time,
        # we're escaping the markup we've just created, so that we don't wrap
        # <p> tags around block-level tags.
        text = self._hash_html_blocks(text)

        text = self._form_paragraphs(text)

        return text

    def _pyshell_block_sub(self, match):
        lines = match.group(0).splitlines(0)
        _dedentlines(lines)
        indent = ' ' * self.tab_width
        s = ('\n' # separate from possible cuddled paragraph
             + indent + ('\n'+indent).join(lines)
             + '\n\n')
        return s

    def _prepare_pyshell_blocks(self, text):
        """Ensure that Python interactive shell sessions are put in
        code blocks -- even if not properly indented.
        """
        if ">>>" not in text:
            return text

        less_than_tab = self.tab_width - 1
        _pyshell_block_re = re.compile(r"""
            ^([ ]{0,%d})>>>[ ].*\n   # first line
            ^(\1.*\S+.*\n)*         # any number of subsequent lines
            ^\n                     # ends with a blank line
            """ % less_than_tab, re.M | re.X)

        return _pyshell_block_re.sub(self._pyshell_block_sub, text)

    def _wiki_table_sub(self, match):
        ttext = match.group(0).strip()
        #print 'wiki table: %r' % match.group(0)
        rows = []
        for line in ttext.splitlines(0):
            line = line.strip()[2:-2].strip()
            row = [c.strip() for c in re.split(r'(?<!\\)\|\|', line)]
            rows.append(row)
        #pprint(rows)
        hlines = ['<table>', '<tbody>']
        for row in rows:
            hrow = ['<tr>']
            for cell in row:
                hrow.append('<td>')
                hrow.append(self._run_span_gamut(cell))
                hrow.append('</td>')
            hrow.append('</tr>')
            hlines.append(''.join(hrow))
        hlines += ['</tbody>', '</table>']
        return '\n'.join(hlines) + '\n'

    def _do_wiki_tables(self, text):
        # Optimization.
        if "||" not in text:
            return text

        less_than_tab = self.tab_width - 1
        wiki_table_re = re.compile(r'''
            (?:(?<=\n\n)|\A\n?)            # leading blank line
            ^([ ]{0,%d})\|\|.+?\|\|[ ]*\n  # first line
            (^\1\|\|.+?\|\|\n)*        # any number of subsequent lines
            ''' % less_than_tab, re.M | re.X)
        return wiki_table_re.sub(self._wiki_table_sub, text)

    def _run_span_gamut(self, text):
        # These are all the transformations that occur *within* block-level
        # tags like paragraphs, headers, and list items.

        text = self._do_code_spans(text)

        text = self._escape_special_chars(text)

        # Process anchor and image tags.
        text = self._do_links(text)

        # Make links out of things like `<http://example.com/>`
        # Must come after _do_links(), because you can use < and >
        # delimiters in inline links like [this](<url>).
        text = self._do_auto_links(text)

        if "link-patterns" in self.extras:
            text = self._do_link_patterns(text)

        text = self._encode_amps_and_angles(text)

        text = self._do_italics_and_bold(text)

        if "smarty-pants" in self.extras:
            text = self._do_smart_punctuation(text)

        # Do hard breaks:
        text = re.sub(r" {2,}\n", " <br%s\n" % self.empty_element_suffix, text)

        return text

    # "Sorta" because auto-links are identified as "tag" tokens.
    _sorta_html_tokenize_re = re.compile(r"""
        (
            # tag
            </?
            (?:\w+)                                     # tag name
            (?:\s+(?:[\w-]+:)?[\w-]+=(?:".*?"|'.*?'))*  # attributes
            \s*/?>
            |
            # auto-link (e.g., <http://www.activestate.com/>)
            <\w+[^>]*>
            |
            <!--.*?-->      # comment
            |
            <\?.*?\?>       # processing instruction
        )
        """, re.X)

    def _escape_special_chars(self, text):
        # Python markdown note: the HTML tokenization here differs from
        # that in Markdown.pl, hence the behaviour for subtle cases can
        # differ (I believe the tokenizer here does a better job because
        # it isn't susceptible to unmatched '<' and '>' in HTML tags).
        # Note, however, that '>' is not allowed in an auto-link URL
        # here.
        escaped = []
        is_html_markup = False
        for token in self._sorta_html_tokenize_re.split(text):
            if is_html_markup:
                # Within tags/HTML-comments/auto-links, encode * and _
                # so they don't conflict with their use in Markdown for
                # italics and strong.  We're replacing each such
                # character with its corresponding MD5 checksum value;
                # this is likely overkill, but it should prevent us from
                # colliding with the escape values by accident.
                escaped.append(token.replace('*', self._escape_table['*'])
                                    .replace('_', self._escape_table['_']))
            else:
                escaped.append(self._encode_backslash_escapes(token))
            is_html_markup = not is_html_markup
        return ''.join(escaped)

    def _hash_html_spans(self, text):
        # Used for safe_mode.

        def _is_auto_link(s):
            if ':' in s and self._auto_link_re.match(s):
                return True
            elif '@' in s and self._auto_email_link_re.match(s):
                return True
            return False

        tokens = []
        is_html_markup = False
        for token in self._sorta_html_tokenize_re.split(text):
            if is_html_markup and not _is_auto_link(token):
                sanitized = self._sanitize_html(token)
                key = _hash_text(sanitized)
                self.html_spans[key] = sanitized
                tokens.append(key)
            else:
                tokens.append(token)
            is_html_markup = not is_html_markup
        return ''.join(tokens)

    def _unhash_html_spans(self, text):
        for key, sanitized in list(self.html_spans.items()):
            text = text.replace(key, sanitized)
        return text

    def _sanitize_html(self, s):
        if self.safe_mode == "replace":
            return self.html_removed_text
        elif self.safe_mode == "escape":
            replacements = [
                ('&', '&amp;'),
                ('<', '&lt;'),
                ('>', '&gt;'),
            ]
            for before, after in replacements:
                s = s.replace(before, after)
            return s
        else:
            raise MarkdownError("invalid value for 'safe_mode': %r (must be "
                                "'escape' or 'replace')" % self.safe_mode)

    _tail_of_inline_link_re = re.compile(r'''
          # Match tail of: [text](/url/) or [text](/url/ "title")
          \(            # literal paren
            [ \t]*
            (?P<url>            # \1
                <.*?>
                |
                .*?
            )
            [ \t]*
            (                   # \2
              (['"])            # quote char = \3
              (?P<title>.*?)
              \3                # matching quote
            )?                  # title is optional
          \)
        ''', re.X | re.S)
    _tail_of_reference_link_re = re.compile(r'''
          # Match tail of: [text][id]
          [ ]?          # one optional space
          (?:\n[ ]*)?   # one optional newline followed by spaces
          \[
            (?P<id>.*?)
          \]
        ''', re.X | re.S)

    def _do_links(self, text):
        """Turn Markdown link shortcuts into XHTML <a> and <img> tags.

        This is a combination of Markdown.pl's _DoAnchors() and
        _DoImages(). They are done together because that simplified the
        approach. It was necessary to use a different approach than
        Markdown.pl because of the lack of atomic matching support in
        Python's regex engine used in $g_nested_brackets.
        """
        MAX_LINK_TEXT_SENTINEL = 3000  # markdown2 issue 24

        # `anchor_allowed_pos` is used to support img links inside
        # anchors, but not anchors inside anchors. An anchor's start
        # pos must be `>= anchor_allowed_pos`.
        anchor_allowed_pos = 0

        curr_pos = 0
        while True: # Handle the next link.
            # The next '[' is the start of:
            # - an inline anchor:   [text](url "title")
            # - a reference anchor: [text][id]
            # - an inline img:      ![text](url "title")
            # - a reference img:    ![text][id]
            # - a footnote ref:     [^id]
            #   (Only if 'footnotes' extra enabled)
            # - a footnote defn:    [^id]: ...
            #   (Only if 'footnotes' extra enabled) These have already
            #   been stripped in _strip_footnote_definitions() so no
            #   need to watch for them.
            # - a link definition:  [id]: url "title"
            #   These have already been stripped in
            #   _strip_link_definitions() so no need to watch for them.
            # - not markup:         [...anything else...
            try:
                start_idx = text.index('[', curr_pos)
            except ValueError:
                break
            text_length = len(text)

            # Find the matching closing ']'.
            # Markdown.pl allows *matching* brackets in link text so we
            # will here too. Markdown.pl *doesn't* currently allow
            # matching brackets in img alt text -- we'll differ in that
            # regard.
            bracket_depth = 0
            for p in range(start_idx+1, min(start_idx+MAX_LINK_TEXT_SENTINEL,
                                            text_length)):
                ch = text[p]
                if ch == ']':
                    bracket_depth -= 1
                    if bracket_depth < 0:
                        break
                elif ch == '[':
                    bracket_depth += 1
            else:
                # Closing bracket not found within sentinel length.
                # This isn't markup.
                curr_pos = start_idx + 1
                continue
            link_text = text[start_idx+1:p]

            # Possibly a footnote ref?
            if "footnotes" in self.extras and link_text.startswith("^"):
                normed_id = re.sub(r'\W', '-', link_text[1:])
                if normed_id in self.footnotes:
                    self.footnote_ids.append(normed_id)
                    result = '<sup class="footnote-ref" id="fnref-%s">' \
                             '<a href="#fn-%s">%s</a></sup>' \
                             % (normed_id, normed_id, len(self.footnote_ids))
                    text = text[:start_idx] + result + text[p+1:]
                else:
                    # This id isn't defined, leave the markup alone.
                    curr_pos = p+1
                continue

            # Now determine what this is by the remainder.
            p += 1
            if p == text_length:
                return text

            # Inline anchor or img?
            if text[p] == '(': # attempt at perf improvement
                match = self._tail_of_inline_link_re.match(text, p)
                if match:
                    # Handle an inline anchor or img.
                    is_img = start_idx > 0 and text[start_idx-1] == "!"
                    if is_img:
                        start_idx -= 1

                    url, title = match.group("url"), match.group("title")
                    if url and url[0] == '<':
                        url = url[1:-1]  # '<url>' -> 'url'
                    # We've got to encode these to avoid conflicting
                    # with italics/bold.
                    url = url.replace('*', self._escape_table['*']) \
                             .replace('_', self._escape_table['_'])
                    if title:
                        title_str = ' title="%s"' % (
                            _xml_escape_attr(title)
                                .replace('*', self._escape_table['*'])
                                .replace('_', self._escape_table['_']))
                    else:
                        title_str = ''
                    if is_img:
                        result = '<img src="%s" alt="%s"%s%s' \
                            % (url.replace('"', '&quot;'),
                               _xml_escape_attr(link_text),
                               title_str, self.empty_element_suffix)
                        if "smarty-pants" in self.extras:
                            result = result.replace('"', self._escape_table['"'])
                        curr_pos = start_idx + len(result)
                        text = text[:start_idx] + result + text[match.end():]
                    elif start_idx >= anchor_allowed_pos:
                        result_head = '<a href="%s"%s>' % (url, title_str)
                        result = '%s%s</a>' % (result_head, link_text)
                        if "smarty-pants" in self.extras:
                            result = result.replace('"', self._escape_table['"'])
                        # <img> allowed from curr_pos on, <a> from
                        # anchor_allowed_pos on.
                        curr_pos = start_idx + len(result_head)
                        anchor_allowed_pos = start_idx + len(result)
                        text = text[:start_idx] + result + text[match.end():]
                    else:
                        # Anchor not allowed here.
                        curr_pos = start_idx + 1
                    continue

            # Reference anchor or img?
            else:
                match = self._tail_of_reference_link_re.match(text, p)
                if match:
                    # Handle a reference-style anchor or img.
                    is_img = start_idx > 0 and text[start_idx-1] == "!"
                    if is_img:
                        start_idx -= 1
                    link_id = match.group("id").lower()
                    if not link_id:
                        link_id = link_text.lower()  # for links like [this][]
                    if link_id in self.urls:
                        url = self.urls[link_id]
                        # We've got to encode these to avoid conflicting
                        # with italics/bold.
                        url = url.replace('*', self._escape_table['*']) \
                                 .replace('_', self._escape_table['_'])
                        title = self.titles.get(link_id)
                        if title:
                            before = title
                            title = _xml_escape_attr(title) \
                                .replace('*', self._escape_table['*']) \
                                .replace('_', self._escape_table['_'])
                            title_str = ' title="%s"' % title
                        else:
                            title_str = ''
                        if is_img:
                            result = '<img src="%s" alt="%s"%s%s' \
                                % (url.replace('"', '&quot;'),
                                   link_text.replace('"', '&quot;'),
                                   title_str, self.empty_element_suffix)
                            if "smarty-pants" in self.extras:
                                result = result.replace('"', self._escape_table['"'])
                            curr_pos = start_idx + len(result)
                            text = text[:start_idx] + result + text[match.end():]
                        elif start_idx >= anchor_allowed_pos:
                            result = '<a href="%s"%s>%s</a>' \
                                % (url, title_str, link_text)
                            result_head = '<a href="%s"%s>' % (url, title_str)
                            result = '%s%s</a>' % (result_head, link_text)
                            if "smarty-pants" in self.extras:
                                result = result.replace('"', self._escape_table['"'])
                            # <img> allowed from curr_pos on, <a> from
                            # anchor_allowed_pos on.
                            curr_pos = start_idx + len(result_head)
                            anchor_allowed_pos = start_idx + len(result)
                            text = text[:start_idx] + result + text[match.end():]
                        else:
                            # Anchor not allowed here.
                            curr_pos = start_idx + 1
                    else:
                        # This id isn't defined, leave the markup alone.
                        curr_pos = match.end()
                    continue

            # Otherwise, it isn't markup.
            curr_pos = start_idx + 1

        return text

    def header_id_from_text(self, text, prefix, n):
        """Generate a header id attribute value from the given header
        HTML content.

        This is only called if the "header-ids" extra is enabled.
        Subclasses may override this for different header ids.

        @param text {str} The text of the header tag
        @param prefix {str} The requested prefix for header ids. This is the
            value of the "header-ids" extra key, if any. Otherwise, None.
        @param n {int} The <hN> tag number, i.e. `1` for an <h1> tag.
        @returns {str} The value for the header tag's "id" attribute. Return
            None to not have an id attribute and to exclude this header from
            the TOC (if the "toc" extra is specified).
        """
        header_id = _slugify(text)
        if prefix and isinstance(prefix, base_string_type):
            header_id = prefix + '-' + header_id
        if header_id in self._count_from_header_id:
            self._count_from_header_id[header_id] += 1
            header_id += '-%s' % self._count_from_header_id[header_id]
        else:
            self._count_from_header_id[header_id] = 1
        return header_id

    _toc = None
    def _toc_add_entry(self, level, id, name):
        if self._toc is None:
            self._toc = []
        self._toc.append((level, id, self._unescape_special_chars(name)))

    _setext_h_re = re.compile(r'^(.+)[ \t]*\n(=+|-+)[ \t]*\n+', re.M)
    def _setext_h_sub(self, match):
        n = {"=": 1, "-": 2}[match.group(2)[0]]
        demote_headers = self.extras.get("demote-headers")
        if demote_headers:
            n = min(n + demote_headers, 6)
        header_id_attr = ""
        if "header-ids" in self.extras:
            header_id = self.header_id_from_text(match.group(1),
                self.extras["header-ids"], n)
            if header_id:
                header_id_attr = ' id="%s"' % header_id
        html = self._run_span_gamut(match.group(1))
        if "toc" in self.extras and header_id:
            self._toc_add_entry(n, header_id, html)
        return "<h%d%s>%s</h%d>\n\n" % (n, header_id_attr, html, n)

    _atx_h_re = re.compile(r'''
        ^(\#{1,6})  # \1 = string of #'s
        [ \t]+
        (.+?)       # \2 = Header text
        [ \t]*
        (?<!\\)     # ensure not an escaped trailing '#'
        \#*         # optional closing #'s (not counted)
        \n+
        ''', re.X | re.M)
    def _atx_h_sub(self, match):
        n = len(match.group(1))
        demote_headers = self.extras.get("demote-headers")
        if demote_headers:
            n = min(n + demote_headers, 6)
        header_id_attr = ""
        if "header-ids" in self.extras:
            header_id = self.header_id_from_text(match.group(2),
                self.extras["header-ids"], n)
            if header_id:
                header_id_attr = ' id="%s"' % header_id
        html = self._run_span_gamut(match.group(2))
        if "toc" in self.extras and header_id:
            self._toc_add_entry(n, header_id, html)
        return "<h%d%s>%s</h%d>\n\n" % (n, header_id_attr, html, n)

    def _do_headers(self, text):
        # Setext-style headers:
        #     Header 1
        #     ========
        #
        #     Header 2
        #     --------
        text = self._setext_h_re.sub(self._setext_h_sub, text)

        # atx-style headers:
        #   # Header 1
        #   ## Header 2
        #   ## Header 2 with closing hashes ##
        #   ...
        #   ###### Header 6
        text = self._atx_h_re.sub(self._atx_h_sub, text)

        return text


    _marker_ul_chars  = '*+-'
    _marker_any = r'(?:[%s]|\d+\.)' % _marker_ul_chars
    _marker_ul = '(?:[%s])' % _marker_ul_chars
    _marker_ol = r'(?:\d+\.)'

    def _list_sub(self, match):
        lst = match.group(1)
        lst_type = match.group(3) in self._marker_ul_chars and "ul" or "ol"
        result = self._process_list_items(lst)
        if self.list_level:
            return "<%s>\n%s</%s>\n" % (lst_type, result, lst_type)
        else:
            return "<%s>\n%s</%s>\n\n" % (lst_type, result, lst_type)

    def _do_lists(self, text):
        # Form HTML ordered (numbered) and unordered (bulleted) lists.

        # Iterate over each *non-overlapping* list match.
        pos = 0
        while True:
            # Find the *first* hit for either list style (ul or ol). We
            # match ul and ol separately to avoid adjacent lists of different
            # types running into each other (see issue #16).
            hits = []
            for marker_pat in (self._marker_ul, self._marker_ol):
                less_than_tab = self.tab_width - 1
                whole_list = r'''
                    (                   # \1 = whole list
                      (                 # \2
                        [ ]{0,%d}
                        (%s)            # \3 = first list item marker
                        [ \t]+
                        (?!\ *\3\ )     # '- - - ...' isn't a list. See 'not_quite_a_list' test case.
                      )
                      (?:.+?)
                      (                 # \4
                          \Z
                        |
                          \n{2,}
                          (?=\S)
                          (?!           # Negative lookahead for another list item marker
                            [ \t]*
                            %s[ \t]+
                          )
                      )
                    )
                ''' % (less_than_tab, marker_pat, marker_pat)
                if self.list_level:  # sub-list
                    list_re = re.compile("^"+whole_list, re.X | re.M | re.S)
                else:
                    list_re = re.compile(r"(?:(?<=\n\n)|\A\n?)"+whole_list,
                                         re.X | re.M | re.S)
                match = list_re.search(text, pos)
                if match:
                    hits.append((match.start(), match))
            if not hits:
                break
            hits.sort()
            match = hits[0][1]
            start, end = match.span()
            text = text[:start] + self._list_sub(match) + text[end:]
            pos = end

        return text

    _list_item_re = re.compile(r'''
        (\n)?                   # leading line = \1
        (^[ \t]*)               # leading whitespace = \2
        (?P<marker>%s) [ \t]+   # list marker = \3
        ((?:.+?)                # list item text = \4
         (\n{1,2}))             # eols = \5
        (?= \n* (\Z | \2 (?P<next_marker>%s) [ \t]+))
        ''' % (_marker_any, _marker_any),
        re.M | re.X | re.S)

    _last_li_endswith_two_eols = False
    def _list_item_sub(self, match):
        item = match.group(4)
        leading_line = match.group(1)
        leading_space = match.group(2)
        if leading_line or "\n\n" in item or self._last_li_endswith_two_eols:
            item = self._run_block_gamut(self._outdent(item))
        else:
            # Recursion for sub-lists:
            item = self._do_lists(self._outdent(item))
            if item.endswith('\n'):
                item = item[:-1]
            item = self._run_span_gamut(item)
        self._last_li_endswith_two_eols = (len(match.group(5)) == 2)
        return "<li>%s</li>\n" % item

    def _process_list_items(self, list_str):
        # Process the contents of a single ordered or unordered list,
        # splitting it into individual list items.

        # The $g_list_level global keeps track of when we're inside a list.
        # Each time we enter a list, we increment it; when we leave a list,
        # we decrement. If it's zero, we're not in a list anymore.
        #
        # We do this because when we're not inside a list, we want to treat
        # something like this:
        #
        #       I recommend upgrading to version
        #       8. Oops, now this line is treated
        #       as a sub-list.
        #
        # As a single paragraph, despite the fact that the second line starts
        # with a digit-period-space sequence.
        #
        # Whereas when we're inside a list (or sub-list), that line will be
        # treated as the start of a sub-list. What a kludge, huh? This is
        # an aspect of Markdown's syntax that's hard to parse perfectly
        # without resorting to mind-reading. Perhaps the solution is to
        # change the syntax rules such that sub-lists must start with a
        # starting cardinal number; e.g. "1." or "a.".
        self.list_level += 1
        self._last_li_endswith_two_eols = False
        list_str = list_str.rstrip('\n') + '\n'
        list_str = self._list_item_re.sub(self._list_item_sub, list_str)
        self.list_level -= 1
        return list_str

    def _get_pygments_lexer(self, lexer_name):
        try:
            from pygments import lexers, util
        except ImportError:
            return None
        try:
            return lexers.get_lexer_by_name(lexer_name)
        except util.ClassNotFound:
            return None

    def _color_with_pygments(self, codeblock, lexer, **formatter_opts):
        import pygments
        import pygments.formatters

        class HtmlCodeFormatter(pygments.formatters.HtmlFormatter):
            def _wrap_code(self, inner):
                """A function for use in a Pygments Formatter which
                wraps in <code> tags.
                """
                yield 0, "<code>"
                for tup in inner:
                    yield tup
                yield 0, "</code>"

            def wrap(self, source, outfile):
                """Return the source with a code, pre, and div."""
                return self._wrap_div(self._wrap_pre(self._wrap_code(source)))

        formatter_opts.setdefault("cssclass", "codehilite")
        formatter = HtmlCodeFormatter(**formatter_opts)
        return pygments.highlight(codeblock, lexer, formatter)

    def _code_block_sub(self, match, is_fenced_code_block=False):
        lexer_name = None
        if is_fenced_code_block:
            lexer_name = match.group(1)
            if lexer_name:
                formatter_opts = self.extras['fenced-code-blocks'] or {}
            codeblock = match.group(2)
            codeblock = codeblock[:-1]  # drop one trailing newline
        else:
            codeblock = match.group(1)
            codeblock = self._outdent(codeblock)
            codeblock = self._detab(codeblock)
            codeblock = codeblock.lstrip('\n')  # trim leading newlines
            codeblock = codeblock.rstrip()      # trim trailing whitespace

            # Note: "code-color" extra is DEPRECATED.
            if "code-color" in self.extras and codeblock.startswith(":::"):
                lexer_name, rest = codeblock.split('\n', 1)
                lexer_name = lexer_name[3:].strip()
                codeblock = rest.lstrip("\n")   # Remove lexer declaration line.
                formatter_opts = self.extras['code-color'] or {}

        if lexer_name:
            lexer = self._get_pygments_lexer(lexer_name)
            if lexer:
                colored = self._color_with_pygments(codeblock, lexer,
                                                    **formatter_opts)
                return "\n\n%s\n\n" % colored

        codeblock = self._encode_code(codeblock)
        pre_class_str = self._html_class_str_from_tag("pre")
        code_class_str = self._html_class_str_from_tag("code")
        return "\n\n<pre%s><code%s>%s\n</code></pre>\n\n" % (
            pre_class_str, code_class_str, codeblock)

    def _html_class_str_from_tag(self, tag):
        """Get the appropriate ' class="..."' string (note the leading
        space), if any, for the given tag.
        """
        if "html-classes" not in self.extras:
            return ""
        try:
            html_classes_from_tag = self.extras["html-classes"]
        except TypeError:
            return ""
        else:
            if tag in html_classes_from_tag:
                return ' class="%s"' % html_classes_from_tag[tag]
        return ""

    def _do_code_blocks(self, text):
        """Process Markdown `<pre><code>` blocks."""
        code_block_re = re.compile(r'''
            (?:\n\n|\A\n?)
            (               # $1 = the code block -- one or more lines, starting with a space/tab
              (?:
                (?:[ ]{%d} | \t)  # Lines must start with a tab or a tab-width of spaces
                .*\n+
              )+
            )
            ((?=^[ ]{0,%d}\S)|\Z)   # Lookahead for non-space at line-start, or end of doc
            ''' % (self.tab_width, self.tab_width),
            re.M | re.X)
        return code_block_re.sub(self._code_block_sub, text)

    _fenced_code_block_re = re.compile(r'''
        (?:\n\n|\A\n?)
        ^```([\w+-]+)?[ \t]*\n      # opening fence, $1 = optional lang
        (.*?)                       # $2 = code block content
        ^```[ \t]*\n                # closing fence
        ''', re.M | re.X | re.S)

    def _fenced_code_block_sub(self, match):
        return self._code_block_sub(match, is_fenced_code_block=True);

    def _do_fenced_code_blocks(self, text):
        """Process ```-fenced unindented code blocks ('fenced-code-blocks' extra)."""
        return self._fenced_code_block_re.sub(self._fenced_code_block_sub, text)

    # Rules for a code span:
    # - backslash escapes are not interpreted in a code span
    # - to include one or or a run of more backticks the delimiters must
    #   be a longer run of backticks
    # - cannot start or end a code span with a backtick; pad with a
    #   space and that space will be removed in the emitted HTML
    # See `test/tm-cases/escapes.text` for a number of edge-case
    # examples.
    _code_span_re = re.compile(r'''
            (?<!\\)
            (`+)        # \1 = Opening run of `
            (?!`)       # See Note A test/tm-cases/escapes.text
            (.+?)       # \2 = The code block
            (?<!`)
            \1          # Matching closer
            (?!`)
        ''', re.X | re.S)

    def _code_span_sub(self, match):
        c = match.group(2).strip(" \t")
        c = self._encode_code(c)
        return "<code>%s</code>" % c

    def _do_code_spans(self, text):
        #   *   Backtick quotes are used for <code></code> spans.
        #
        #   *   You can use multiple backticks as the delimiters if you want to
        #       include literal backticks in the code span. So, this input:
        #
        #         Just type ``foo `bar` baz`` at the prompt.
        #
        #       Will translate to:
        #
        #         <p>Just type <code>foo `bar` baz</code> at the prompt.</p>
        #
        #       There's no arbitrary limit to the number of backticks you
        #       can use as delimters. If you need three consecutive backticks
        #       in your code, use four for delimiters, etc.
        #
        #   *   You can use spaces to get literal backticks at the edges:
        #
        #         ... type `` `bar` `` ...
        #
        #       Turns to:
        #
        #         ... type <code>`bar`</code> ...
        return self._code_span_re.sub(self._code_span_sub, text)

    def _encode_code(self, text):
        """Encode/escape certain characters inside Markdown code runs.
        The point is that in code, these characters are literals,
        and lose their special Markdown meanings.
        """
        replacements = [
            # Encode all ampersands; HTML entities are not
            # entities within a Markdown code span.
            ('&', '&amp;'),
            # Do the angle bracket song and dance:
            ('<', '&lt;'),
            ('>', '&gt;'),
        ]
        for before, after in replacements:
            text = text.replace(before, after)
        hashed = _hash_text(text)
        self._escape_table[text] = hashed
        return hashed

    _strong_re = re.compile(r"(\*\*|__)(?=\S)(.+?[*_]*)(?<=\S)\1", re.S)
    _em_re = re.compile(r"(\*|_)(?=\S)(.+?)(?<=\S)\1", re.S)
    _code_friendly_strong_re = re.compile(r"\*\*(?=\S)(.+?[*_]*)(?<=\S)\*\*", re.S)
    _code_friendly_em_re = re.compile(r"\*(?=\S)(.+?)(?<=\S)\*", re.S)
    def _do_italics_and_bold(self, text):
        # <strong> must go first:
        if "code-friendly" in self.extras:
            text = self._code_friendly_strong_re.sub(r"<strong>\1</strong>", text)
            text = self._code_friendly_em_re.sub(r"<em>\1</em>", text)
        else:
            text = self._strong_re.sub(r"<strong>\2</strong>", text)
            text = self._em_re.sub(r"<em>\2</em>", text)
        return text

    # "smarty-pants" extra: Very liberal in interpreting a single prime as an
    # apostrophe; e.g. ignores the fact that "round", "bout", "twer", and
    # "twixt" can be written without an initial apostrophe. This is fine because
    # using scare quotes (single quotation marks) is rare.
    _apostrophe_year_re = re.compile(r"'(\d\d)(?=(\s|,|;|\.|\?|!|$))")
    _contractions = ["tis", "twas", "twer", "neath", "o", "n",
        "round", "bout", "twixt", "nuff", "fraid", "sup"]
    def _do_smart_contractions(self, text):
        text = self._apostrophe_year_re.sub(r"&#8217;\1", text)
        for c in self._contractions:
            text = text.replace("'%s" % c, "&#8217;%s" % c)
            text = text.replace("'%s" % c.capitalize(),
                "&#8217;%s" % c.capitalize())
        return text

    # Substitute double-quotes before single-quotes.
    _opening_single_quote_re = re.compile(r"(?<!\S)'(?=\S)")
    _opening_double_quote_re = re.compile(r'(?<!\S)"(?=\S)')
    _closing_single_quote_re = re.compile(r"(?<=\S)'")
    _closing_double_quote_re = re.compile(r'(?<=\S)"(?=(\s|,|;|\.|\?|!|$))')
    def _do_smart_punctuation(self, text):
        """Fancifies 'single quotes', "double quotes", and apostrophes.
        Converts --, ---, and ... into en dashes, em dashes, and ellipses.

        Inspiration is: <http://daringfireball.net/projects/smartypants/>
        See "test/tm-cases/smarty_pants.text" for a full discussion of the
        support here and
        <http://code.google.com/p/python-markdown2/issues/detail?id=42> for a
        discussion of some diversion from the original SmartyPants.
        """
        if "'" in text: # guard for perf
            text = self._do_smart_contractions(text)
            text = self._opening_single_quote_re.sub("&#8216;", text)
            text = self._closing_single_quote_re.sub("&#8217;", text)

        if '"' in text: # guard for perf
            text = self._opening_double_quote_re.sub("&#8220;", text)
            text = self._closing_double_quote_re.sub("&#8221;", text)

        text = text.replace("---", "&#8212;")
        text = text.replace("--", "&#8211;")
        text = text.replace("...", "&#8230;")
        text = text.replace(" . . . ", "&#8230;")
        text = text.replace(". . .", "&#8230;")
        return text

    _block_quote_re = re.compile(r'''
        (                           # Wrap whole match in \1
          (
            ^[ \t]*>[ \t]?          # '>' at the start of a line
              .+\n                  # rest of the first line
            (.+\n)*                 # subsequent consecutive lines
            \n*                     # blanks
          )+
        )
        ''', re.M | re.X)
    _bq_one_level_re = re.compile('^[ \t]*>[ \t]?', re.M);

    _html_pre_block_re = re.compile(r'(\s*<pre>.+?</pre>)', re.S)
    def _dedent_two_spaces_sub(self, match):
        return re.sub(r'(?m)^  ', '', match.group(1))

    def _block_quote_sub(self, match):
        bq = match.group(1)
        bq = self._bq_one_level_re.sub('', bq)  # trim one level of quoting
        bq = self._ws_only_line_re.sub('', bq)  # trim whitespace-only lines
        bq = self._run_block_gamut(bq)          # recurse

        bq = re.sub('(?m)^', '  ', bq)
        # These leading spaces screw with <pre> content, so we need to fix that:
        bq = self._html_pre_block_re.sub(self._dedent_two_spaces_sub, bq)

        return "<blockquote>\n%s\n</blockquote>\n\n" % bq

    def _do_block_quotes(self, text):
        if '>' not in text:
            return text
        return self._block_quote_re.sub(self._block_quote_sub, text)

    def _form_paragraphs(self, text):
        # Strip leading and trailing lines:
        text = text.strip('\n')

        # Wrap <p> tags.
        grafs = []
        for i, graf in enumerate(re.split(r"\n{2,}", text)):
            if graf in self.html_blocks:
                # Unhashify HTML blocks
                grafs.append(self.html_blocks[graf])
            else:
                cuddled_list = None
                if "cuddled-lists" in self.extras:
                    # Need to put back trailing '\n' for `_list_item_re`
                    # match at the end of the paragraph.
                    li = self._list_item_re.search(graf + '\n')
                    # Two of the same list marker in this paragraph: a likely
                    # candidate for a list cuddled to preceding paragraph
                    # text (issue 33). Note the `[-1]` is a quick way to
                    # consider numeric bullets (e.g. "1." and "2.") to be
                    # equal.
                    if (li and len(li.group(2)) <= 3 and li.group("next_marker")
                        and li.group("marker")[-1] == li.group("next_marker")[-1]):
                        start = li.start()
                        cuddled_list = self._do_lists(graf[start:]).rstrip("\n")
                        assert cuddled_list.startswith("<ul>") or cuddled_list.startswith("<ol>")
                        graf = graf[:start]

                # Wrap <p> tags.
                graf = self._run_span_gamut(graf)
                grafs.append("<p>" + graf.lstrip(" \t") + "</p>")

                if cuddled_list:
                    grafs.append(cuddled_list)

        return "\n\n".join(grafs)

    def _add_footnotes(self, text):
        if self.footnotes:
            footer = [
                '<div class="footnotes">',
                '<hr' + self.empty_element_suffix,
                '<ol>',
            ]
            for i, id in enumerate(self.footnote_ids):
                if i != 0:
                    footer.append('')
                footer.append('<li id="fn-%s">' % id)
                footer.append(self._run_block_gamut(self.footnotes[id]))
                backlink = ('<a href="#fnref-%s" '
                    'class="footnoteBackLink" '
                    'title="Jump back to footnote %d in the text.">'
                    '&#8617;</a>' % (id, i+1))
                if footer[-1].endswith("</p>"):
                    footer[-1] = footer[-1][:-len("</p>")] \
                        + '&nbsp;' + backlink + "</p>"
                else:
                    footer.append("\n<p>%s</p>" % backlink)
                footer.append('</li>')
            footer.append('</ol>')
            footer.append('</div>')
            return text + '\n\n' + '\n'.join(footer)
        else:
            return text

    # Ampersand-encoding based entirely on Nat Irons's Amputator MT plugin:
    #   http://bumppo.net/projects/amputator/
    _ampersand_re = re.compile(r'&(?!#?[xX]?(?:[0-9a-fA-F]+|\w+);)')
    _naked_lt_re = re.compile(r'<(?![a-z/?\$!])', re.I)
    _naked_gt_re = re.compile(r'''(?<![a-z0-9?!/'"-])>''', re.I)

    def _encode_amps_and_angles(self, text):
        # Smart processing for ampersands and angle brackets that need
        # to be encoded.
        text = self._ampersand_re.sub('&amp;', text)

        # Encode naked <'s
        text = self._naked_lt_re.sub('&lt;', text)

        # Encode naked >'s
        # Note: Other markdown implementations (e.g. Markdown.pl, PHP
        # Markdown) don't do this.
        text = self._naked_gt_re.sub('&gt;', text)
        return text

    def _encode_backslash_escapes(self, text):
        for ch, escape in list(self._escape_table.items()):
            text = text.replace("\\"+ch, escape)
        return text

    _auto_link_re = re.compile(r'<((https?|ftp):[^\'">\s]+)>', re.I)
    def _auto_link_sub(self, match):
        g1 = match.group(1)
        return '<a href="%s">%s</a>' % (g1, g1)

    _auto_email_link_re = re.compile(r"""
          <
           (?:mailto:)?
          (
              [-.\w]+
              \@
              [-\w]+(\.[-\w]+)*\.[a-z]+
          )
          >
        """, re.I | re.X | re.U)
    def _auto_email_link_sub(self, match):
        return self._encode_email_address(
            self._unescape_special_chars(match.group(1)))

    def _do_auto_links(self, text):
        text = self._auto_link_re.sub(self._auto_link_sub, text)
        text = self._auto_email_link_re.sub(self._auto_email_link_sub, text)
        return text

    def _encode_email_address(self, addr):
        #  Input: an email address, e.g. "foo@example.com"
        #
        #  Output: the email address as a mailto link, with each character
        #      of the address encoded as either a decimal or hex entity, in
        #      the hopes of foiling most address harvesting spam bots. E.g.:
        #
        #    <a href="&#x6D;&#97;&#105;&#108;&#x74;&#111;:&#102;&#111;&#111;&#64;&#101;
        #       x&#x61;&#109;&#x70;&#108;&#x65;&#x2E;&#99;&#111;&#109;">&#102;&#111;&#111;
        #       &#64;&#101;x&#x61;&#109;&#x70;&#108;&#x65;&#x2E;&#99;&#111;&#109;</a>
        #
        #  Based on a filter by Matthew Wickline, posted to the BBEdit-Talk
        #  mailing list: <http://tinyurl.com/yu7ue>
        chars = [_xml_encode_email_char_at_random(ch)
                 for ch in "mailto:" + addr]
        # Strip the mailto: from the visible part.
        addr = '<a href="%s">%s</a>' \
               % (''.join(chars), ''.join(chars[7:]))
        return addr

    def _do_link_patterns(self, text):
        """Caveat emptor: there isn't much guarding against link
        patterns being formed inside other standard Markdown links, e.g.
        inside a [link def][like this].

        Dev Notes: *Could* consider prefixing regexes with a negative
        lookbehind assertion to attempt to guard against this.
        """
        link_from_hash = {}
        for regex, repl in self.link_patterns:
            replacements = []
            for match in regex.finditer(text):
                if hasattr(repl, "__call__"):
                    href = repl(match)
                else:
                    href = match.expand(repl)
                replacements.append((match.span(), href))
            for (start, end), href in reversed(replacements):
                escaped_href = (
                    href.replace('"', '&quot;')  # b/c of attr quote
                        # To avoid markdown <em> and <strong>:
                        .replace('*', self._escape_table['*'])
                        .replace('_', self._escape_table['_']))
                link = '<a href="%s">%s</a>' % (escaped_href, text[start:end])
                hash = _hash_text(link)
                link_from_hash[hash] = link
                text = text[:start] + hash + text[end:]
        for hash, link in list(link_from_hash.items()):
            text = text.replace(hash, link)
        return text

    def _unescape_special_chars(self, text):
        # Swap back in all the special characters we've hidden.
        for ch, hash in list(self._escape_table.items()):
            text = text.replace(hash, ch)
        return text

    def _outdent(self, text):
        # Remove one level of line-leading tabs or spaces
        return self._outdent_re.sub('', text)


class MarkdownWithExtras(Markdown):
    """A markdowner class that enables most extras:

    - footnotes
    - code-color (only has effect if 'pygments' Python module on path)

    These are not included:
    - pyshell (specific to Python-related documenting)
    - code-friendly (because it *disables* part of the syntax)
    - link-patterns (because you need to specify some actual
      link-patterns anyway)
    """
    extras = ["footnotes", "code-color"]


#---- internal support functions

class UnicodeWithAttrs(unicode):
    """A subclass of unicode used for the return value of conversion to
    possibly attach some attributes. E.g. the "toc_html" attribute when
    the "toc" extra is used.
    """
    metadata = None
    _toc = None
    def toc_html(self):
        """Return the HTML for the current TOC.

        This expects the `_toc` attribute to have been set on this instance.
        """
        if self._toc is None:
            return None

        def indent():
            return '  ' * (len(h_stack) - 1)
        lines = []
        h_stack = [0]   # stack of header-level numbers
        for level, id, name in self._toc:
            if level > h_stack[-1]:
                lines.append("%s<ul>" % indent())
                h_stack.append(level)
            elif level == h_stack[-1]:
                lines[-1] += "</li>"
            else:
                while level < h_stack[-1]:
                    h_stack.pop()
                    if not lines[-1].endswith("</li>"):
                        lines[-1] += "</li>"
                    lines.append("%s</ul></li>" % indent())
            lines.append('%s<li><a href="#%s">%s</a>' % (
                indent(), id, name))
        while len(h_stack) > 1:
            h_stack.pop()
            if not lines[-1].endswith("</li>"):
                lines[-1] += "</li>"
            lines.append("%s</ul>" % indent())
        return '\n'.join(lines) + '\n'
    toc_html = property(toc_html)

## {{{ http://code.activestate.com/recipes/577257/ (r1)
import re

char_map = {u'À': 'A', u'Á': 'A', u'Â': 'A', u'Ã': 'A', u'Ä': 'Ae', u'Å': 'A', u'Æ': 'A', u'Ā': 'A', u'Ą': 'A', u'Ă': 'A', u'Ç': 'C', u'Ć': 'C', u'Č': 'C', u'Ĉ': 'C', u'Ċ': 'C', u'Ď': 'D', u'Đ': 'D', u'È': 'E', u'É': 'E', u'Ê': 'E', u'Ë': 'E', u'Ē': 'E', u'Ę': 'E', u'Ě': 'E', u'Ĕ': 'E', u'Ė': 'E', u'Ĝ': 'G', u'Ğ': 'G', u'Ġ': 'G', u'Ģ': 'G', u'Ĥ': 'H', u'Ħ': 'H', u'Ì': 'I', u'Í': 'I', u'Î': 'I', u'Ï': 'I', u'Ī': 'I', u'Ĩ': 'I', u'Ĭ': 'I', u'Į': 'I', u'İ': 'I', u'Ĳ': 'IJ', u'Ĵ': 'J', u'Ķ': 'K', u'Ľ': 'K', u'Ĺ': 'K', u'Ļ': 'K', u'Ŀ': 'K', u'Ł': 'L', u'Ñ': 'N', u'Ń': 'N', u'Ň': 'N', u'Ņ': 'N', u'Ŋ': 'N', u'Ò': 'O', u'Ó': 'O', u'Ô': 'O', u'Õ': 'O', u'Ö': 'Oe', u'Ø': 'O', u'Ō': 'O', u'Ő': 'O', u'Ŏ': 'O', u'Œ': 'OE', u'Ŕ': 'R', u'Ř': 'R', u'Ŗ': 'R', u'Ś': 'S', u'Ş': 'S', u'Ŝ': 'S', u'Ș': 'S', u'Š': 'S', u'Ť': 'T', u'Ţ': 'T', u'Ŧ': 'T', u'Ț': 'T', u'Ù': 'U', u'Ú': 'U', u'Û': 'U', u'Ü': 'Ue', u'Ū': 'U', u'Ů': 'U', u'Ű': 'U', u'Ŭ': 'U', u'Ũ': 'U', u'Ų': 'U', u'Ŵ': 'W', u'Ŷ': 'Y', u'Ÿ': 'Y', u'Ý': 'Y', u'Ź': 'Z', u'Ż': 'Z', u'Ž': 'Z', u'à': 'a', u'á': 'a', u'â': 'a', u'ã': 'a', u'ä': 'ae', u'ā': 'a', u'ą': 'a', u'ă': 'a', u'å': 'a', u'æ': 'ae', u'ç': 'c', u'ć': 'c', u'č': 'c', u'ĉ': 'c', u'ċ': 'c', u'ď': 'd', u'đ': 'd', u'è': 'e', u'é': 'e', u'ê': 'e', u'ë': 'e', u'ē': 'e', u'ę': 'e', u'ě': 'e', u'ĕ': 'e', u'ė': 'e', u'ƒ': 'f', u'ĝ': 'g', u'ğ': 'g', u'ġ': 'g', u'ģ': 'g', u'ĥ': 'h', u'ħ': 'h', u'ì': 'i', u'í': 'i', u'î': 'i', u'ï': 'i', u'ī': 'i', u'ĩ': 'i', u'ĭ': 'i', u'į': 'i', u'ı': 'i', u'ĳ': 'ij', u'ĵ': 'j', u'ķ': 'k', u'ĸ': 'k', u'ł': 'l', u'ľ': 'l', u'ĺ': 'l', u'ļ': 'l', u'ŀ': 'l', u'ñ': 'n', u'ń': 'n', u'ň': 'n', u'ņ': 'n', u'ŉ': 'n', u'ŋ': 'n', u'ò': 'o', u'ó': 'o', u'ô': 'o', u'õ': 'o', u'ö': 'oe', u'ø': 'o', u'ō': 'o', u'ő': 'o', u'ŏ': 'o', u'œ': 'oe', u'ŕ': 'r', u'ř': 'r', u'ŗ': 'r', u'ś': 's', u'š': 's', u'ť': 't', u'ù': 'u', u'ú': 'u', u'û': 'u', u'ü': 'ue', u'ū': 'u', u'ů': 'u', u'ű': 'u', u'ŭ': 'u', u'ũ': 'u', u'ų': 'u', u'ŵ': 'w', u'ÿ': 'y', u'ý': 'y', u'ŷ': 'y', u'ż': 'z', u'ź': 'z', u'ž': 'z', u'ß': 'ss', u'ſ': 'ss', u'Α': 'A', u'Ά': 'A', u'Ἀ': 'A', u'Ἁ': 'A', u'Ἂ': 'A', u'Ἃ': 'A', u'Ἄ': 'A', u'Ἅ': 'A', u'Ἆ': 'A', u'Ἇ': 'A', u'ᾈ': 'A', u'ᾉ': 'A', u'ᾊ': 'A', u'ᾋ': 'A', u'ᾌ': 'A', u'ᾍ': 'A', u'ᾎ': 'A', u'ᾏ': 'A', u'Ᾰ': 'A', u'Ᾱ': 'A', u'Ὰ': 'A', u'Ά': 'A', u'ᾼ': 'A', u'Β': 'B', u'Γ': 'G', u'Δ': 'D', u'Ε': 'E', u'Έ': 'E', u'Ἐ': 'E', u'Ἑ': 'E', u'Ἒ': 'E', u'Ἓ': 'E', u'Ἔ': 'E', u'Ἕ': 'E', u'Έ': 'E', u'Ὲ': 'E', u'Ζ': 'Z', u'Η': 'I', u'Ή': 'I', u'Ἠ': 'I', u'Ἡ': 'I', u'Ἢ': 'I', u'Ἣ': 'I', u'Ἤ': 'I', u'Ἥ': 'I', u'Ἦ': 'I', u'Ἧ': 'I', u'ᾘ': 'I', u'ᾙ': 'I', u'ᾚ': 'I', u'ᾛ': 'I', u'ᾜ': 'I', u'ᾝ': 'I', u'ᾞ': 'I', u'ᾟ': 'I', u'Ὴ': 'I', u'Ή': 'I', u'ῌ': 'I', u'Θ': 'TH', u'Ι': 'I', u'Ί': 'I', u'Ϊ': 'I', u'Ἰ': 'I', u'Ἱ': 'I', u'Ἲ': 'I', u'Ἳ': 'I', u'Ἴ': 'I', u'Ἵ': 'I', u'Ἶ': 'I', u'Ἷ': 'I', u'Ῐ': 'I', u'Ῑ': 'I', u'Ὶ': 'I', u'Ί': 'I', u'Κ': 'K', u'Λ': 'L', u'Μ': 'M', u'Ν': 'N', u'Ξ': 'KS', u'Ο': 'O', u'Ό': 'O', u'Ὀ': 'O', u'Ὁ': 'O', u'Ὂ': 'O', u'Ὃ': 'O', u'Ὄ': 'O', u'Ὅ': 'O', u'Ὸ': 'O', u'Ό': 'O', u'Π': 'P', u'Ρ': 'R', u'Ῥ': 'R', u'Σ': 'S', u'Τ': 'T', u'Υ': 'Y', u'Ύ': 'Y', u'Ϋ': 'Y', u'Ὑ': 'Y', u'Ὓ': 'Y', u'Ὕ': 'Y', u'Ὗ': 'Y', u'Ῠ': 'Y', u'Ῡ': 'Y', u'Ὺ': 'Y', u'Ύ': 'Y', u'Φ': 'F', u'Χ': 'X', u'Ψ': 'PS', u'Ω': 'O', u'Ώ': 'O', u'Ὠ': 'O', u'Ὡ': 'O', u'Ὢ': 'O', u'Ὣ': 'O', u'Ὤ': 'O', u'Ὥ': 'O', u'Ὦ': 'O', u'Ὧ': 'O', u'ᾨ': 'O', u'ᾩ': 'O', u'ᾪ': 'O', u'ᾫ': 'O', u'ᾬ': 'O', u'ᾭ': 'O', u'ᾮ': 'O', u'ᾯ': 'O', u'Ὼ': 'O', u'Ώ': 'O', u'ῼ': 'O', u'α': 'a', u'ά': 'a', u'ἀ': 'a', u'ἁ': 'a', u'ἂ': 'a', u'ἃ': 'a', u'ἄ': 'a', u'ἅ': 'a', u'ἆ': 'a', u'ἇ': 'a', u'ᾀ': 'a', u'ᾁ': 'a', u'ᾂ': 'a', u'ᾃ': 'a', u'ᾄ': 'a', u'ᾅ': 'a', u'ᾆ': 'a', u'ᾇ': 'a', u'ὰ': 'a', u'ά': 'a', u'ᾰ': 'a', u'ᾱ': 'a', u'ᾲ': 'a', u'ᾳ': 'a', u'ᾴ': 'a', u'ᾶ': 'a', u'ᾷ': 'a', u'β': 'b', u'γ': 'g', u'δ': 'd', u'ε': 'e', u'έ': 'e', u'ἐ': 'e', u'ἑ': 'e', u'ἒ': 'e', u'ἓ': 'e', u'ἔ': 'e', u'ἕ': 'e', u'ὲ': 'e', u'έ': 'e', u'ζ': 'z', u'η': 'i', u'ή': 'i', u'ἠ': 'i', u'ἡ': 'i', u'ἢ': 'i', u'ἣ': 'i', u'ἤ': 'i', u'ἥ': 'i', u'ἦ': 'i', u'ἧ': 'i', u'ᾐ': 'i', u'ᾑ': 'i', u'ᾒ': 'i', u'ᾓ': 'i', u'ᾔ': 'i', u'ᾕ': 'i', u'ᾖ': 'i', u'ᾗ': 'i', u'ὴ': 'i', u'ή': 'i', u'ῂ': 'i', u'ῃ': 'i', u'ῄ': 'i', u'ῆ': 'i', u'ῇ': 'i', u'θ': 'th', u'ι': 'i', u'ί': 'i', u'ϊ': 'i', u'ΐ': 'i', u'ἰ': 'i', u'ἱ': 'i', u'ἲ': 'i', u'ἳ': 'i', u'ἴ': 'i', u'ἵ': 'i', u'ἶ': 'i', u'ἷ': 'i', u'ὶ': 'i', u'ί': 'i', u'ῐ': 'i', u'ῑ': 'i', u'ῒ': 'i', u'ΐ': 'i', u'ῖ': 'i', u'ῗ': 'i', u'κ': 'k', u'λ': 'l', u'μ': 'm', u'ν': 'n', u'ξ': 'ks', u'ο': 'o', u'ό': 'o', u'ὀ': 'o', u'ὁ': 'o', u'ὂ': 'o', u'ὃ': 'o', u'ὄ': 'o', u'ὅ': 'o', u'ὸ': 'o', u'ό': 'o', u'π': 'p', u'ρ': 'r', u'ῤ': 'r', u'ῥ': 'r', u'σ': 's', u'ς': 's', u'τ': 't', u'υ': 'y', u'ύ': 'y', u'ϋ': 'y', u'ΰ': 'y', u'ὐ': 'y', u'ὑ': 'y', u'ὒ': 'y', u'ὓ': 'y', u'ὔ': 'y', u'ὕ': 'y', u'ὖ': 'y', u'ὗ': 'y', u'ὺ': 'y', u'ύ': 'y', u'ῠ': 'y', u'ῡ': 'y', u'ῢ': 'y', u'ΰ': 'y', u'ῦ': 'y', u'ῧ': 'y', u'φ': 'f', u'χ': 'x', u'ψ': 'ps', u'ω': 'o', u'ώ': 'o', u'ὠ': 'o', u'ὡ': 'o', u'ὢ': 'o', u'ὣ': 'o', u'ὤ': 'o', u'ὥ': 'o', u'ὦ': 'o', u'ὧ': 'o', u'ᾠ': 'o', u'ᾡ': 'o', u'ᾢ': 'o', u'ᾣ': 'o', u'ᾤ': 'o', u'ᾥ': 'o', u'ᾦ': 'o', u'ᾧ': 'o', u'ὼ': 'o', u'ώ': 'o', u'ῲ': 'o', u'ῳ': 'o', u'ῴ': 'o', u'ῶ': 'o', u'ῷ': 'o', u'¨': '', u'΅': '', u'᾿': '', u'῾': '', u'῍': '', u'῝': '', u'῎': '', u'῞': '', u'῏': '', u'῟': '', u'῀': '', u'῁': '', u'΄': '', u'΅': '', u'`': '', u'῭': '', u'ͺ': '', u'᾽': '', u'А': 'A', u'Б': 'B', u'В': 'V', u'Г': 'G', u'Д': 'D', u'Е': 'E', u'Ё': 'YO', u'Ж': 'ZH', u'З': 'Z', u'И': 'I', u'Й': 'J', u'К': 'K', u'Л': 'L', u'М': 'M', u'Н': 'N', u'О': 'O', u'П': 'P', u'Р': 'R', u'С': 'S', u'Т': 'T', u'У': 'U', u'Ф': 'F', u'Х': 'H', u'Ц': 'TS', u'Ч': 'CH', u'Ш': 'SH', u'Щ': 'SCH', u'Ы': 'YI', u'Э': 'E', u'Ю': 'YU', u'Я': 'YA', u'а': 'A', u'б': 'B', u'в': 'V', u'г': 'G', u'д': 'D', u'е': 'E', u'ё': 'YO', u'ж': 'ZH', u'з': 'Z', u'и': 'I', u'й': 'J', u'к': 'K', u'л': 'L', u'м': 'M', u'н': 'N', u'о': 'O', u'п': 'P', u'р': 'R', u'с': 'S', u'т': 'T', u'у': 'U', u'ф': 'F', u'х': 'H', u'ц': 'TS', u'ч': 'CH', u'ш': 'SH', u'щ': 'SCH', u'ы': 'YI', u'э': 'E', u'ю': 'YU', u'я': 'YA', u'Ъ': '', u'ъ': '', u'Ь': '', u'ь': '', u'ð': 'd', u'Ð': 'D', u'þ': 'th', u'Þ': 'TH',u'ა': 'a', u'ბ': 'b', u'გ': 'g', u'დ': 'd', u'ე': 'e', u'ვ': 'v', u'ზ': 'z', u'თ': 't', u'ი': 'i', u'კ': 'k', u'ლ': 'l', u'მ': 'm', u'ნ': 'n', u'ო': 'o', u'პ': 'p', u'ჟ': 'zh', u'რ': 'r', u'ს': 's', u'ტ': 't', u'უ': 'u', u'ფ': 'p', u'ქ': 'k', u'ღ': 'gh', u'ყ': 'q', u'შ': 'sh', u'ჩ': 'ch', u'ც': 'ts', u'ძ': 'dz', u'წ': 'ts', u'ჭ': 'ch', u'ხ': 'kh', u'ჯ': 'j', u'ჰ': 'h' }

def replace_char(m):
    char = m.group()
    if char_map.has_key(char):
        return char_map[char]
    else:
        return char

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def _slugify(text, delim=u'-'):
    """Generates an ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = word.encode('utf-8')
        if word:
            result.append(word)
    slugified = delim.join([i.decode('utf-8') for i in result])
    return re.sub('[^a-zA-Z0-9\\s\\-]{1}', replace_char, slugified).lower()
## end of http://code.activestate.com/recipes/577257/ }}}


# From http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52549
def _curry(*args, **kwargs):
    function, args = args[0], args[1:]
    def result(*rest, **kwrest):
        combined = kwargs.copy()
        combined.update(kwrest)
        return function(*args + rest, **combined)
    return result

# Recipe: regex_from_encoded_pattern (1.0)
def _regex_from_encoded_pattern(s):
    """'foo'    -> re.compile(re.escape('foo'))
       '/foo/'  -> re.compile('foo')
       '/foo/i' -> re.compile('foo', re.I)
    """
    if s.startswith('/') and s.rfind('/') != 0:
        # Parse it: /PATTERN/FLAGS
        idx = s.rfind('/')
        pattern, flags_str = s[1:idx], s[idx+1:]
        flag_from_char = {
            "i": re.IGNORECASE,
            "l": re.LOCALE,
            "s": re.DOTALL,
            "m": re.MULTILINE,
            "u": re.UNICODE,
        }
        flags = 0
        for char in flags_str:
            try:
                flags |= flag_from_char[char]
            except KeyError:
                raise ValueError("unsupported regex flag: '%s' in '%s' "
                                 "(must be one of '%s')"
                                 % (char, s, ''.join(list(flag_from_char.keys()))))
        return re.compile(s[1:idx], flags)
    else: # not an encoded regex
        return re.compile(re.escape(s))

# Recipe: dedent (0.1.2)
def _dedentlines(lines, tabsize=8, skip_first_line=False):
    """_dedentlines(lines, tabsize=8, skip_first_line=False) -> dedented lines

        "lines" is a list of lines to dedent.
        "tabsize" is the tab width to use for indent width calculations.
        "skip_first_line" is a boolean indicating if the first line should
            be skipped for calculating the indent width and for dedenting.
            This is sometimes useful for docstrings and similar.

    Same as dedent() except operates on a sequence of lines. Note: the
    lines list is modified **in-place**.
    """
    DEBUG = False
    if DEBUG:
        print("dedent: dedent(..., tabsize=%d, skip_first_line=%r)"\
              % (tabsize, skip_first_line))
    indents = []
    margin = None
    for i, line in enumerate(lines):
        if i == 0 and skip_first_line: continue
        indent = 0
        for ch in line:
            if ch == ' ':
                indent += 1
            elif ch == '\t':
                indent += tabsize - (indent % tabsize)
            elif ch in '\r\n':
                continue # skip all-whitespace lines
            else:
                break
        else:
            continue # skip all-whitespace lines
        if DEBUG: print("dedent: indent=%d: %r" % (indent, line))
        if margin is None:
            margin = indent
        else:
            margin = min(margin, indent)
    if DEBUG: print("dedent: margin=%r" % margin)

    if margin is not None and margin > 0:
        for i, line in enumerate(lines):
            if i == 0 and skip_first_line: continue
            removed = 0
            for j, ch in enumerate(line):
                if ch == ' ':
                    removed += 1
                elif ch == '\t':
                    removed += tabsize - (removed % tabsize)
                elif ch in '\r\n':
                    if DEBUG: print("dedent: %r: EOL -> strip up to EOL" % line)
                    lines[i] = lines[i][j:]
                    break
                else:
                    raise ValueError("unexpected non-whitespace char %r in "
                                     "line %r while removing %d-space margin"
                                     % (ch, line, margin))
                if DEBUG:
                    print("dedent: %r: %r -> removed %d/%d"\
                          % (line, ch, removed, margin))
                if removed == margin:
                    lines[i] = lines[i][j+1:]
                    break
                elif removed > margin:
                    lines[i] = ' '*(removed-margin) + lines[i][j+1:]
                    break
            else:
                if removed:
                    lines[i] = lines[i][removed:]
    return lines

def _dedent(text, tabsize=8, skip_first_line=False):
    """_dedent(text, tabsize=8, skip_first_line=False) -> dedented text

        "text" is the text to dedent.
        "tabsize" is the tab width to use for indent width calculations.
        "skip_first_line" is a boolean indicating if the first line should
            be skipped for calculating the indent width and for dedenting.
            This is sometimes useful for docstrings and similar.

    textwrap.dedent(s), but don't expand tabs to spaces
    """
    lines = text.splitlines(1)
    _dedentlines(lines, tabsize=tabsize, skip_first_line=skip_first_line)
    return ''.join(lines)


class _memoized:
   """Decorator that caches a function's return value each time it is called.
   If called later with the same arguments, the cached value is returned, and
   not re-evaluated.

   http://wiki.python.org/moin/PythonDecoratorLibrary
   """
   def __init__(self, func):
      self.func = func
      self.cache = {}
   def __call__(self, *args):
      try:
         return self.cache[args]
      except KeyError:
         self.cache[args] = value = self.func(*args)
         return value
      except TypeError:
         # uncachable -- for instance, passing a list as an argument.
         # Better to not cache than to blow up entirely.
         return self.func(*args)
   def __repr__(self):
      """Return the function's docstring."""
      return self.func.__doc__


def _xml_oneliner_re_from_tab_width(tab_width):
    """Standalone XML processing instruction regex."""
    return re.compile(r"""
        (?:
            (?<=\n\n)       # Starting after a blank line
            |               # or
            \A\n?           # the beginning of the doc
        )
        (                           # save in $1
            [ ]{0,%d}
            (?:
                <\?\w+\b\s+.*?\?>   # XML processing instruction
                |
                <\w+:\w+\b\s+.*?/>  # namespaced single tag
            )
            [ \t]*
            (?=\n{2,}|\Z)       # followed by a blank line or end of document
        )
        """ % (tab_width - 1), re.X)
_xml_oneliner_re_from_tab_width = _memoized(_xml_oneliner_re_from_tab_width)

def _hr_tag_re_from_tab_width(tab_width):
     return re.compile(r"""
        (?:
            (?<=\n\n)       # Starting after a blank line
            |               # or
            \A\n?           # the beginning of the doc
        )
        (                       # save in \1
            [ ]{0,%d}
            <(hr)               # start tag = \2
            \b                  # word break
            ([^<>])*?           #
            /?>                 # the matching end tag
            [ \t]*
            (?=\n{2,}|\Z)       # followed by a blank line or end of document
        )
        """ % (tab_width - 1), re.X)
_hr_tag_re_from_tab_width = _memoized(_hr_tag_re_from_tab_width)


def _xml_escape_attr(attr, skip_single_quote=True):
    """Escape the given string for use in an HTML/XML tag attribute.

    By default this doesn't bother with escaping `'` to `&#39;`, presuming that
    the tag attribute is surrounded by double quotes.
    """
    escaped = (attr
        .replace('&', '&amp;')
        .replace('"', '&quot;')
        .replace('<', '&lt;')
        .replace('>', '&gt;'))
    if not skip_single_quote:
        escaped = escaped.replace("'", "&#39;")
    return escaped


def _xml_encode_email_char_at_random(ch):
    r = random()
    # Roughly 10% raw, 45% hex, 45% dec.
    # '@' *must* be encoded. I [John Gruber] insist.
    # Issue 26: '_' must be encoded.
    if r > 0.9 and ch not in "@_":
        return ch
    elif r < 0.45:
        # The [1:] is to drop leading '0': 0x63 -> x63
        return '&#%s;' % hex(ord(ch))[1:]
    else:
        return '&#%s;' % ord(ch)



#---- mainline

class _NoReflowFormatter(optparse.IndentedHelpFormatter):
    """An optparse formatter that does NOT reflow the description."""
    def format_description(self, description):
        return description or ""

def _test():
    import doctest
    doctest.testmod()

def main(argv=None):
    if argv is None:
        argv = sys.argv
    if not logging.root.handlers:
        logging.basicConfig()

    usage = "usage: %prog [PATHS...]"
    version = "%prog "+__version__
    parser = optparse.OptionParser(prog="markdown2", usage=usage,
        version=version, description=cmdln_desc,
        formatter=_NoReflowFormatter())
    parser.add_option("-v", "--verbose", dest="log_level",
                      action="store_const", const=logging.DEBUG,
                      help="more verbose output")
    parser.add_option("--encoding",
                      help="specify encoding of text content")
    parser.add_option("--html4tags", action="store_true", default=False,
                      help="use HTML 4 style for empty element tags")
    parser.add_option("-s", "--safe", metavar="MODE", dest="safe_mode",
                      help="sanitize literal HTML: 'escape' escapes "
                           "HTML meta chars, 'replace' replaces with an "
                           "[HTML_REMOVED] note")
    parser.add_option("-x", "--extras", action="append",
                      help="Turn on specific extra features (not part of "
                           "the core Markdown spec). See above.")
    parser.add_option("--use-file-vars",
                      help="Look for and use Emacs-style 'markdown-extras' "
                           "file var to turn on extras. See "
                           "<https://github.com/trentm/python-markdown2/wiki/Extras>")
    parser.add_option("--link-patterns-file",
                      help="path to a link pattern file")
    parser.add_option("--self-test", action="store_true",
                      help="run internal self-tests (some doctests)")
    parser.add_option("--compare", action="store_true",
                      help="run against Markdown.pl as well (for testing)")
    parser.set_defaults(log_level=logging.INFO, compare=False,
                        encoding="utf-8", safe_mode=None, use_file_vars=False)
    opts, paths = parser.parse_args()
    log.setLevel(opts.log_level)

    if opts.self_test:
        return _test()

    if opts.extras:
        extras = {}
        for s in opts.extras:
            splitter = re.compile("[,;: ]+")
            for e in splitter.split(s):
                if '=' in e:
                    ename, earg = e.split('=', 1)
                    try:
                        earg = int(earg)
                    except ValueError:
                        pass
                else:
                    ename, earg = e, None
                extras[ename] = earg
    else:
        extras = None

    if opts.link_patterns_file:
        link_patterns = []
        f = open(opts.link_patterns_file)
        try:
            for i, line in enumerate(f.readlines()):
                if not line.strip(): continue
                if line.lstrip().startswith("#"): continue
                try:
                    pat, href = line.rstrip().rsplit(None, 1)
                except ValueError:
                    raise MarkdownError("%s:%d: invalid link pattern line: %r"
                                        % (opts.link_patterns_file, i+1, line))
                link_patterns.append(
                    (_regex_from_encoded_pattern(pat), href))
        finally:
            f.close()
    else:
        link_patterns = None

    from os.path import join, dirname, abspath, exists
    markdown_pl = join(dirname(dirname(abspath(__file__))), "test",
                       "Markdown.pl")
    if not paths:
        paths = ['-']
    for path in paths:
        if path == '-':
            text = sys.stdin.read()
        else:
            fp = codecs.open(path, 'r', opts.encoding)
            text = fp.read()
            fp.close()
        if opts.compare:
            from subprocess import Popen, PIPE
            print("==== Markdown.pl ====")
            p = Popen('perl %s' % markdown_pl, shell=True, stdin=PIPE, stdout=PIPE, close_fds=True)
            p.stdin.write(text.encode('utf-8'))
            p.stdin.close()
            perl_html = p.stdout.read().decode('utf-8')
            if py3:
                sys.stdout.write(perl_html)
            else:
                sys.stdout.write(perl_html.encode(
                    sys.stdout.encoding or "utf-8", 'xmlcharrefreplace'))
            print("==== markdown2.py ====")
        html = markdown(text,
            html4tags=opts.html4tags,
            safe_mode=opts.safe_mode,
            extras=extras, link_patterns=link_patterns,
            use_file_vars=opts.use_file_vars)
        if py3:
            sys.stdout.write(html)
        else:
            sys.stdout.write(html.encode(
                sys.stdout.encoding or "utf-8", 'xmlcharrefreplace'))
        if extras and "toc" in extras:
            log.debug("toc_html: " +
                html.toc_html.encode(sys.stdout.encoding or "utf-8", 'xmlcharrefreplace'))
        if opts.compare:
            test_dir = join(dirname(dirname(abspath(__file__))), "test")
            if exists(join(test_dir, "test_markdown2.py")):
                sys.path.insert(0, test_dir)
                from test_markdown2 import norm_html_from_html
                norm_html = norm_html_from_html(html)
                norm_perl_html = norm_html_from_html(perl_html)
            else:
                norm_html = html
                norm_perl_html = perl_html
            print("==== match? %r ====" % (norm_perl_html == norm_html))


template_html = u'''<!DOCTYPE html>
<!--
Backdoc is a tool for backbone-like documentation generation. 
Backdoc main goal is to help to generate one page documentation from one markdown source file.

https://github.com/chibisov/backdoc
-->
<html lang="ru">
<head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="HandheldFriendly" content="true" />
    <title><!-- title --></title>

    <!-- Bootstrap -->
    <style type="text/css">
/*!
 * Bootstrap v3.0.0
 *
 * Copyright 2013 Twitter, Inc
 * Licensed under the Apache License v2.0
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Designed and built with all the love in the world by @mdo and @fat.
 *//*! normalize.css v2.1.0 | MIT License | git.io/normalize */
 article,aside,details,figcaption,figure,footer,header,hgroup,main,nav,section,summary{display:block}audio,canvas,video{display:inline-block}audio:not([controls]){display:none;height:0}[hidden]{display:none}html{font-family:sans-serif;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%}body{margin:0}a:focus{outline:thin dotted}a:active,a:hover{outline:0}h1{margin:.67em 0;font-size:2em}abbr[title]{border-bottom:1px dotted}b,strong{font-weight:bold}dfn{font-style:italic}hr{height:0;-moz-box-sizing:content-box;box-sizing:content-box}mark{color:#000;background:#ff0}code,kbd,pre,samp{font-family:monospace,serif;font-size:1em}pre{white-space:pre-wrap}q{quotes:"\201C" "\201D" "\2018" "\2019"}small{font-size:80%}sub,sup{position:relative;font-size:75%;line-height:0;vertical-align:baseline}sup{top:-0.5em}sub{bottom:-0.25em}img{border:0}svg:not(:root){overflow:hidden}figure{margin:0}fieldset{padding:.35em .625em .75em;margin:0 2px;border:1px solid #c0c0c0}legend{padding:0;border:0}button,input,select,textarea{margin:0;font-family:inherit;font-size:100%}button,input{line-height:normal}button,select{text-transform:none}button,html input[type="button"],input[type="reset"],input[type="submit"]{cursor:pointer;-webkit-appearance:button}button[disabled],html input[disabled]{cursor:default}input[type="checkbox"],input[type="radio"]{padding:0;box-sizing:border-box}input[type="search"]{-webkit-box-sizing:content-box;-moz-box-sizing:content-box;box-sizing:content-box;-webkit-appearance:textfield}input[type="search"]::-webkit-search-cancel-button,input[type="search"]::-webkit-search-decoration{-webkit-appearance:none}button::-moz-focus-inner,input::-moz-focus-inner{padding:0;border:0}textarea{overflow:auto;vertical-align:top}table{border-collapse:collapse;border-spacing:0}@media print{*{color:#000!important;text-shadow:none!important;background:transparent!important;box-shadow:none!important}a,a:visited{text-decoration:underline}a[href]:after{content:" (" attr(href) ")"}abbr[title]:after{content:" (" attr(title) ")"}.ir a:after,a[href^="javascript:"]:after,a[href^="#"]:after{content:""}pre,blockquote{border:1px solid #999;page-break-inside:avoid}thead{display:table-header-group}tr,img{page-break-inside:avoid}img{max-width:100%!important}@page{margin:2cm .5cm}p,h2,h3{orphans:3;widows:3}h2,h3{page-break-after:avoid}.navbar{display:none}.table td,.table th{background-color:#fff!important}.btn>.caret,.dropup>.btn>.caret{border-top-color:#000!important}.label{border:1px solid #000}.table{border-collapse:collapse!important}.table-bordered th,.table-bordered td{border:1px solid #ddd!important}}*{-webkit-box-sizing:border-box;-moz-box-sizing:border-box;box-sizing:border-box}html{font-size:62.5%;-webkit-tap-highlight-color:rgba(0,0,0,0)}body{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-size:14px;line-height:1.428571429;color:#333;background-color:#fff}input,button,select,textarea{font-family:inherit;font-size:inherit;line-height:inherit}a{color:#428bca;text-decoration:none}a:hover,a:focus{color:#2a6496;text-decoration:underline}a:focus{outline:thin dotted #333;outline:5px auto -webkit-focus-ring-color;outline-offset:-2px}img{vertical-align:middle}.img-responsive{display:inline-block;height:auto;max-width:100%}.img-rounded{border-radius:6px}.img-circle{border-radius:500px}hr{margin-top:20px;margin-bottom:20px;border:0;border-top:1px solid #eee}p{margin:0 0 10px}.lead{margin-bottom:20px;font-size:16.099999999999998px;font-weight:200;line-height:1.4}@media(min-width:768px){.lead{font-size:21px}}small{font-size:85%}cite{font-style:normal}.text-muted{color:#999}.text-primary{color:#428bca}.text-warning{color:#c09853}.text-danger{color:#b94a48}.text-success{color:#468847}.text-info{color:#3a87ad}.text-left{text-align:left}.text-right{text-align:right}.text-center{text-align:center}h1,h2,h3,h4,h5,h6,.h1,.h2,.h3,.h4,.h5,.h6{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-weight:500;line-height:1.1}h1 small,h2 small,h3 small,h4 small,h5 small,h6 small,.h1 small,.h2 small,.h3 small,.h4 small,.h5 small,.h6 small{font-weight:normal;line-height:1;color:#999}h1,h2,h3{margin-top:20px;margin-bottom:10px}h4,h5,h6{margin-top:10px;margin-bottom:10px}h1,.h1{font-size:38px}h2,.h2{font-size:32px}h3,.h3{font-size:24px}h4,.h4{font-size:18px}h5,.h5{font-size:14px}h6,.h6{font-size:12px}h1 small,.h1 small{font-size:24px}h2 small,.h2 small{font-size:18px}h3 small,.h3 small,h4 small,.h4 small{font-size:14px}.page-header{padding-bottom:9px;margin:40px 0 20px;border-bottom:1px solid #eee}ul,ol{margin-top:0;margin-bottom:10px}ul ul,ol ul,ul ol,ol ol{margin-bottom:0}.list-unstyled{padding-left:0;list-style:none}.list-inline{padding-left:0;list-style:none}.list-inline>li{display:inline-block;padding-right:5px;padding-left:5px}dl{margin-bottom:20px}dt,dd{line-height:1.428571429}dt{font-weight:bold}dd{margin-left:0}.dl-horizontal dt{float:left;width:160px;overflow:hidden;clear:left;text-align:right;text-overflow:ellipsis;white-space:nowrap}.dl-horizontal dd{margin-left:180px}.dl-horizontal dd:before,.dl-horizontal dd:after{display:table;content:" "}.dl-horizontal dd:after{clear:both}.dl-horizontal dd:before,.dl-horizontal dd:after{display:table;content:" "}.dl-horizontal dd:after{clear:both}abbr[title],abbr[data-original-title]{cursor:help;border-bottom:1px dotted #999}abbr.initialism{font-size:90%;text-transform:uppercase}blockquote{padding:10px 20px;margin:0 0 20px;border-left:5px solid #eee}blockquote p{font-size:17.5px;font-weight:300;line-height:1.25}blockquote p:last-child{margin-bottom:0}blockquote small{display:block;line-height:1.428571429;color:#999}blockquote small:before{content:'\2014 \00A0'}blockquote.pull-right{float:right;padding-right:15px;padding-left:0;border-right:5px solid #eee;border-left:0}blockquote.pull-right p,blockquote.pull-right small{text-align:right}blockquote.pull-right small:before{content:''}blockquote.pull-right small:after{content:'\00A0 \2014'}q:before,q:after,blockquote:before,blockquote:after{content:""}address{display:block;margin-bottom:20px;font-style:normal;line-height:1.428571429}code,pre{font-family:Monaco,Menlo,Consolas,"Courier New",monospace}code{padding:2px 4px;font-size:90%;color:#c7254e;white-space:nowrap;background-color:#f9f2f4;border-radius:4px}pre{display:block;padding:9.5px;margin:0 0 10px;font-size:13px;line-height:1.428571429;color:#333;word-break:break-all;word-wrap:break-word;background-color:#f5f5f5;border:1px solid #ccc;border-radius:4px}pre.prettyprint{margin-bottom:20px}pre code{padding:0;color:inherit;white-space:pre-wrap;background-color:transparent;border:0}.pre-scrollable{max-height:340px;overflow-y:scroll}.container{margin-right:auto;margin-left:auto}.container:before,.container:after{display:table;content:" "}.container:after{clear:both}.container:before,.container:after{display:table;content:" "}.container:after{clear:both}.row:before,.row:after{display:table;content:" "}.row:after{clear:both}.row:before,.row:after{display:table;content:" "}.row:after{clear:both}@media(min-width:768px){.row{margin-right:-15px;margin-left:-15px}}.row .row{margin-right:-15px;margin-left:-15px}.col-1,.col-2,.col-3,.col-4,.col-5,.col-6,.col-7,.col-8,.col-9,.col-10,.col-11,.col-12,.col-sm-1,.col-sm-2,.col-sm-3,.col-sm-4,.col-sm-5,.col-sm-6,.col-sm-7,.col-sm-8,.col-sm-9,.col-sm-10,.col-sm-11,.col-sm-12,.col-lg-1,.col-lg-2,.col-lg-3,.col-lg-4,.col-lg-5,.col-lg-6,.col-lg-7,.col-lg-8,.col-lg-9,.col-lg-10,.col-lg-11,.col-lg-12{position:relative;min-height:1px;padding-right:15px;padding-left:15px}.col-1,.col-2,.col-3,.col-4,.col-5,.col-6,.col-7,.col-8,.col-9,.col-10,.col-11,.col-12{float:left}.col-1{width:8.333333333333332%}.col-2{width:16.666666666666664%}.col-3{width:25%}.col-4{width:33.33333333333333%}.col-5{width:41.66666666666667%}.col-6{width:50%}.col-7{width:58.333333333333336%}.col-8{width:66.66666666666666%}.col-9{width:75%}.col-10{width:83.33333333333334%}.col-11{width:91.66666666666666%}.col-12{width:100%}@media(min-width:768px){.container{max-width:728px}.col-sm-1,.col-sm-2,.col-sm-3,.col-sm-4,.col-sm-5,.col-sm-6,.col-sm-7,.col-sm-8,.col-sm-9,.col-sm-10,.col-sm-11,.col-sm-12{float:left}.col-sm-1{width:8.333333333333332%}.col-sm-2{width:16.666666666666664%}.col-sm-3{width:25%}.col-sm-4{width:33.33333333333333%}.col-sm-5{width:41.66666666666667%}.col-sm-6{width:50%}.col-sm-7{width:58.333333333333336%}.col-sm-8{width:66.66666666666666%}.col-sm-9{width:75%}.col-sm-10{width:83.33333333333334%}.col-sm-11{width:91.66666666666666%}.col-sm-12{width:100%}.col-push-1{left:8.333333333333332%}.col-push-2{left:16.666666666666664%}.col-push-3{left:25%}.col-push-4{left:33.33333333333333%}.col-push-5{left:41.66666666666667%}.col-push-6{left:50%}.col-push-7{left:58.333333333333336%}.col-push-8{left:66.66666666666666%}.col-push-9{left:75%}.col-push-10{left:83.33333333333334%}.col-push-11{left:91.66666666666666%}.col-pull-1{right:8.333333333333332%}.col-pull-2{right:16.666666666666664%}.col-pull-3{right:25%}.col-pull-4{right:33.33333333333333%}.col-pull-5{right:41.66666666666667%}.col-pull-6{right:50%}.col-pull-7{right:58.333333333333336%}.col-pull-8{right:66.66666666666666%}.col-pull-9{right:75%}.col-pull-10{right:83.33333333333334%}.col-pull-11{right:91.66666666666666%}}@media(min-width:992px){.container{max-width:940px}.col-lg-1,.col-lg-2,.col-lg-3,.col-lg-4,.col-lg-5,.col-lg-6,.col-lg-7,.col-lg-8,.col-lg-9,.col-lg-10,.col-lg-11,.col-lg-12{float:left}.col-lg-1{width:8.333333333333332%}.col-lg-2{width:16.666666666666664%}.col-lg-3{width:25%}.col-lg-4{width:33.33333333333333%}.col-lg-5{width:41.66666666666667%}.col-lg-6{width:50%}.col-lg-7{width:58.333333333333336%}.col-lg-8{width:66.66666666666666%}.col-lg-9{width:75%}.col-lg-10{width:83.33333333333334%}.col-lg-11{width:91.66666666666666%}.col-lg-12{width:100%}.col-offset-1{margin-left:8.333333333333332%}.col-offset-2{margin-left:16.666666666666664%}.col-offset-3{margin-left:25%}.col-offset-4{margin-left:33.33333333333333%}.col-offset-5{margin-left:41.66666666666667%}.col-offset-6{margin-left:50%}.col-offset-7{margin-left:58.333333333333336%}.col-offset-8{margin-left:66.66666666666666%}.col-offset-9{margin-left:75%}.col-offset-10{margin-left:83.33333333333334%}.col-offset-11{margin-left:91.66666666666666%}}@media(min-width:1200px){.container{max-width:1170px}}table{max-width:100%;background-color:transparent}th{text-align:left}.table{width:100%;margin-bottom:20px}.table thead>tr>th,.table tbody>tr>th,.table tfoot>tr>th,.table thead>tr>td,.table tbody>tr>td,.table tfoot>tr>td{padding:8px;line-height:1.428571429;vertical-align:top;border-top:1px solid #ddd}.table thead>tr>th{vertical-align:bottom}.table caption+thead tr:first-child th,.table colgroup+thead tr:first-child th,.table thead:first-child tr:first-child th,.table caption+thead tr:first-child td,.table colgroup+thead tr:first-child td,.table thead:first-child tr:first-child td{border-top:0}.table tbody+tbody{border-top:2px solid #ddd}.table .table{background-color:#fff}.table-condensed thead>tr>th,.table-condensed tbody>tr>th,.table-condensed tfoot>tr>th,.table-condensed thead>tr>td,.table-condensed tbody>tr>td,.table-condensed tfoot>tr>td{padding:5px}.table-bordered{border:1px solid #ddd}.table-bordered>thead>tr>th,.table-bordered>tbody>tr>th,.table-bordered>tfoot>tr>th,.table-bordered>thead>tr>td,.table-bordered>tbody>tr>td,.table-bordered>tfoot>tr>td{border:1px solid #ddd}.table-striped>tbody>tr:nth-child(odd)>td,.table-striped>tbody>tr:nth-child(odd)>th{background-color:#f9f9f9}.table-hover>tbody>tr:hover>td,.table-hover>tbody>tr:hover>th{background-color:#f5f5f5}table col[class^="col-"]{display:table-column;float:none}table td[class^="col-"],table th[class^="col-"]{display:table-cell;float:none}.table>thead>tr>td.active,.table>tbody>tr>td.active,.table>tfoot>tr>td.active,.table>thead>tr>th.active,.table>tbody>tr>th.active,.table>tfoot>tr>th.active,.table>thead>tr.active>td,.table>tbody>tr.active>td,.table>tfoot>tr.active>td,.table>thead>tr.active>th,.table>tbody>tr.active>th,.table>tfoot>tr.active>th{background-color:#f5f5f5}.table>thead>tr>td.success,.table>tbody>tr>td.success,.table>tfoot>tr>td.success,.table>thead>tr>th.success,.table>tbody>tr>th.success,.table>tfoot>tr>th.success,.table>thead>tr.success>td,.table>tbody>tr.success>td,.table>tfoot>tr.success>td,.table>thead>tr.success>th,.table>tbody>tr.success>th,.table>tfoot>tr.success>th{background-color:#dff0d8;border-color:#d6e9c6}.table>thead>tr>td.danger,.table>tbody>tr>td.danger,.table>tfoot>tr>td.danger,.table>thead>tr>th.danger,.table>tbody>tr>th.danger,.table>tfoot>tr>th.danger,.table>thead>tr.danger>td,.table>tbody>tr.danger>td,.table>tfoot>tr.danger>td,.table>thead>tr.danger>th,.table>tbody>tr.danger>th,.table>tfoot>tr.danger>th{background-color:#f2dede;border-color:#eed3d7}.table>thead>tr>td.warning,.table>tbody>tr>td.warning,.table>tfoot>tr>td.warning,.table>thead>tr>th.warning,.table>tbody>tr>th.warning,.table>tfoot>tr>th.warning,.table>thead>tr.warning>td,.table>tbody>tr.warning>td,.table>tfoot>tr.warning>td,.table>thead>tr.warning>th,.table>tbody>tr.warning>th,.table>tfoot>tr.warning>th{background-color:#fcf8e3;border-color:#fbeed5}.table-hover>tbody>tr>td.success:hover,.table-hover>tbody>tr>th.success:hover,.table-hover>tbody>tr.success:hover>td{background-color:#d0e9c6;border-color:#c9e2b3}.table-hover>tbody>tr>td.danger:hover,.table-hover>tbody>tr>th.danger:hover,.table-hover>tbody>tr.danger:hover>td{background-color:#ebcccc;border-color:#e6c1c7}.table-hover>tbody>tr>td.warning:hover,.table-hover>tbody>tr>th.warning:hover,.table-hover>tbody>tr.warning:hover>td{background-color:#faf2cc;border-color:#f8e5be}fieldset{padding:0;margin:0;border:0}legend{display:block;width:100%;padding:0;margin-bottom:20px;font-size:21px;line-height:inherit;color:#333;border:0;border-bottom:1px solid #e5e5e5}label{display:inline-block;margin-bottom:5px;font-weight:bold}input[type="search"]{-webkit-box-sizing:border-box;-moz-box-sizing:border-box;box-sizing:border-box}input[type="radio"],input[type="checkbox"]{margin:4px 0 0;margin-top:1px \9;line-height:normal}input[type="file"]{display:block}select[multiple],select[size]{height:auto}select optgroup{font-family:inherit;font-size:inherit;font-style:inherit}input[type="file"]:focus,input[type="radio"]:focus,input[type="checkbox"]:focus{outline:thin dotted #333;outline:5px auto -webkit-focus-ring-color;outline-offset:-2px}input[type="number"]::-webkit-outer-spin-button,input[type="number"]::-webkit-inner-spin-button{height:auto}.form-control:-moz-placeholder{color:#999}.form-control::-moz-placeholder{color:#999}.form-control:-ms-input-placeholder{color:#999}.form-control::-webkit-input-placeholder{color:#999}.form-control{display:block;width:100%;height:38px;padding:8px 12px;font-size:14px;line-height:1.428571429;color:#555;vertical-align:middle;background-color:#fff;border:1px solid #ccc;border-radius:4px;-webkit-box-shadow:inset 0 1px 1px rgba(0,0,0,0.075);box-shadow:inset 0 1px 1px rgba(0,0,0,0.075);-webkit-transition:border-color ease-in-out .15s,box-shadow ease-in-out .15s;transition:border-color ease-in-out .15s,box-shadow ease-in-out .15s}.form-control:focus{border-color:rgba(82,168,236,0.8);outline:0;-webkit-box-shadow:inset 0 1px 1px rgba(0,0,0,0.075),0 0 8px rgba(82,168,236,0.6);box-shadow:inset 0 1px 1px rgba(0,0,0,0.075),0 0 8px rgba(82,168,236,0.6)}.form-control[disabled],.form-control[readonly],fieldset[disabled] .form-control{cursor:not-allowed;background-color:#eee}textarea.form-control{height:auto}.form-group{margin-bottom:15px}.radio,.checkbox{display:block;min-height:20px;padding-left:20px;margin-top:10px;margin-bottom:10px;vertical-align:middle}.radio label,.checkbox label{display:inline;margin-bottom:0;font-weight:normal;cursor:pointer}.radio input[type="radio"],.radio-inline input[type="radio"],.checkbox input[type="checkbox"],.checkbox-inline input[type="checkbox"]{float:left;margin-left:-20px}.radio+.radio,.checkbox+.checkbox{margin-top:-5px}.radio-inline,.checkbox-inline{display:inline-block;padding-left:20px;margin-bottom:0;font-weight:normal;vertical-align:middle;cursor:pointer}.radio-inline+.radio-inline,.checkbox-inline+.checkbox-inline{margin-top:0;margin-left:10px}.form-control.input-large{height:56px;padding:14px 16px;font-size:18px;border-radius:6px}.form-control.input-small{height:30px;padding:5px 10px;font-size:12px;border-radius:3px}select.input-large{height:56px;line-height:56px}select.input-small{height:30px;line-height:30px}.has-warning .help-block,.has-warning .control-label{color:#c09853}.has-warning .form-control{padding-right:32px;border-color:#c09853;-webkit-box-shadow:inset 0 1px 1px rgba(0,0,0,0.075);box-shadow:inset 0 1px 1px rgba(0,0,0,0.075)}.has-warning .form-control:focus{border-color:#a47e3c;-webkit-box-shadow:inset 0 1px 1px rgba(0,0,0,0.075),0 0 6px #dbc59e;box-shadow:inset 0 1px 1px rgba(0,0,0,0.075),0 0 6px #dbc59e}.has-warning .input-group-addon{color:#c09853;background-color:#fcf8e3;border-color:#c09853}.has-error .help-block,.has-error .control-label{color:#b94a48}.has-error .form-control{padding-right:32px;border-color:#b94a48;-webkit-box-shadow:inset 0 1px 1px rgba(0,0,0,0.075);box-shadow:inset 0 1px 1px rgba(0,0,0,0.075)}.has-error .form-control:focus{border-color:#953b39;-webkit-box-shadow:inset 0 1px 1px rgba(0,0,0,0.075),0 0 6px #d59392;box-shadow:inset 0 1px 1px rgba(0,0,0,0.075),0 0 6px #d59392}.has-error .input-group-addon{color:#b94a48;background-color:#f2dede;border-color:#b94a48}.has-success .help-block,.has-success .control-label{color:#468847}.has-success .form-control{padding-right:32px;border-color:#468847;-webkit-box-shadow:inset 0 1px 1px rgba(0,0,0,0.075);box-shadow:inset 0 1px 1px rgba(0,0,0,0.075)}.has-success .form-control:focus{border-color:#356635;-webkit-box-shadow:inset 0 1px 1px rgba(0,0,0,0.075),0 0 6px #7aba7b;box-shadow:inset 0 1px 1px rgba(0,0,0,0.075),0 0 6px #7aba7b}.has-success .input-group-addon{color:#468847;background-color:#dff0d8;border-color:#468847}.help-block{display:block;margin-top:5px;margin-bottom:10px;color:#737373}.input-group{display:table;border-collapse:separate}.input-group.col{float:none;padding-right:0;padding-left:0}.input-group .form-control{width:100%;margin-bottom:0}.input-group-addon,.input-group-btn,.input-group .form-control{display:table-cell}.input-group-addon:not(:first-child):not(:last-child),.input-group-btn:not(:first-child):not(:last-child),.input-group .form-control:not(:first-child):not(:last-child){border-radius:0}.input-group-addon,.input-group-btn{width:1%;white-space:nowrap;vertical-align:middle}.input-group-addon{padding:8px 12px;font-size:14px;font-weight:normal;line-height:1.428571429;text-align:center;background-color:#eee;border:1px solid #ccc;border-radius:4px;-webkit-box-sizing:border-box;-moz-box-sizing:border-box;box-sizing:border-box}.input-group-addon.input-small{padding:5px 10px;font-size:12px;border-radius:3px}.input-group-addon.input-large{padding:14px 16px;font-size:18px;border-radius:6px}.input-group .form-control:first-child,.input-group-addon:first-child,.input-group-btn:first-child>.btn,.input-group-btn:first-child>.dropdown-toggle,.input-group-btn:last-child>.btn:not(:last-child):not(.dropdown-toggle){border-top-right-radius:0;border-bottom-right-radius:0}.input-group-addon:first-child{border-right:0}.input-group .form-control:last-child,.input-group-addon:last-child,.input-group-btn:last-child>.btn,.input-group-btn:last-child>.dropdown-toggle,.input-group-btn:first-child>.btn:not(:first-child){border-bottom-left-radius:0;border-top-left-radius:0}.input-group-addon:last-child{border-left:0}.input-group-btn{position:relative;white-space:nowrap}.input-group-btn>.btn{position:relative}.input-group-btn>.btn+.btn{margin-left:-4px}.input-group-btn>.btn:hover,.input-group-btn>.btn:active{z-index:2}.form-inline .form-control,.form-inline .radio,.form-inline .checkbox{display:inline-block}.form-inline .radio,.form-inline .checkbox{margin-top:0;margin-bottom:0}.form-horizontal .control-label{padding-top:6px}.form-horizontal .form-group:before,.form-horizontal .form-group:after{display:table;content:" "}.form-horizontal .form-group:after{clear:both}.form-horizontal .form-group:before,.form-horizontal .form-group:after{display:table;content:" "}.form-horizontal .form-group:after{clear:both}@media(min-width:768px){.form-horizontal .form-group{margin-right:-15px;margin-left:-15px}}.form-horizontal .form-group .row{margin-right:-15px;margin-left:-15px}@media(min-width:768px){.form-horizontal .control-label{text-align:right}}.btn{display:inline-block;padding:8px 12px;margin-bottom:0;font-size:14px;font-weight:500;line-height:1.428571429;text-align:center;white-space:nowrap;vertical-align:middle;cursor:pointer;border:1px solid transparent;border-radius:4px}.btn:focus{outline:thin dotted #333;outline:5px auto -webkit-focus-ring-color;outline-offset:-2px}.btn:hover,.btn:focus{color:#fff;text-decoration:none}.btn:active,.btn.active{outline:0;-webkit-box-shadow:inset 0 3px 5px rgba(0,0,0,0.125);box-shadow:inset 0 3px 5px rgba(0,0,0,0.125)}.btn.disabled,.btn[disabled],fieldset[disabled] .btn{pointer-events:none;cursor:default;opacity:.65;filter:alpha(opacity=65);-webkit-box-shadow:none;box-shadow:none}.btn-default{color:#fff;background-color:#474949;border-color:#474949}.btn-default:hover,.btn-default:focus,.btn-default:active,.btn-default.active{background-color:#3a3c3c;border-color:#2e2f2f}.btn-default.disabled,.btn-default[disabled],fieldset[disabled] .btn-default,.btn-default.disabled:hover,.btn-default[disabled]:hover,fieldset[disabled] .btn-default:hover,.btn-default.disabled:focus,.btn-default[disabled]:focus,fieldset[disabled] .btn-default:focus,.btn-default.disabled:active,.btn-default[disabled]:active,fieldset[disabled] .btn-default:active,.btn-default.disabled.active,.btn-default[disabled].active,fieldset[disabled] .btn-default.active{background-color:#474949;border-color:#474949}.btn-primary{color:#fff;background-color:#428bca;border-color:#428bca}.btn-primary:hover,.btn-primary:focus,.btn-primary:active,.btn-primary.active{background-color:#357ebd;border-color:#3071a9}.btn-primary.disabled,.btn-primary[disabled],fieldset[disabled] .btn-primary,.btn-primary.disabled:hover,.btn-primary[disabled]:hover,fieldset[disabled] .btn-primary:hover,.btn-primary.disabled:focus,.btn-primary[disabled]:focus,fieldset[disabled] .btn-primary:focus,.btn-primary.disabled:active,.btn-primary[disabled]:active,fieldset[disabled] .btn-primary:active,.btn-primary.disabled.active,.btn-primary[disabled].active,fieldset[disabled] .btn-primary.active{background-color:#428bca;border-color:#428bca}.btn-warning{color:#fff;background-color:#f0ad4e;border-color:#f0ad4e}.btn-warning:hover,.btn-warning:focus,.btn-warning:active,.btn-warning.active{background-color:#eea236;border-color:#ec971f}.btn-warning.disabled,.btn-warning[disabled],fieldset[disabled] .btn-warning,.btn-warning.disabled:hover,.btn-warning[disabled]:hover,fieldset[disabled] .btn-warning:hover,.btn-warning.disabled:focus,.btn-warning[disabled]:focus,fieldset[disabled] .btn-warning:focus,.btn-warning.disabled:active,.btn-warning[disabled]:active,fieldset[disabled] .btn-warning:active,.btn-warning.disabled.active,.btn-warning[disabled].active,fieldset[disabled] .btn-warning.active{background-color:#f0ad4e;border-color:#f0ad4e}.btn-danger{color:#fff;background-color:#d9534f;border-color:#d9534f}.btn-danger:hover,.btn-danger:focus,.btn-danger:active,.btn-danger.active{background-color:#d43f3a;border-color:#c9302c}.btn-danger.disabled,.btn-danger[disabled],fieldset[disabled] .btn-danger,.btn-danger.disabled:hover,.btn-danger[disabled]:hover,fieldset[disabled] .btn-danger:hover,.btn-danger.disabled:focus,.btn-danger[disabled]:focus,fieldset[disabled] .btn-danger:focus,.btn-danger.disabled:active,.btn-danger[disabled]:active,fieldset[disabled] .btn-danger:active,.btn-danger.disabled.active,.btn-danger[disabled].active,fieldset[disabled] .btn-danger.active{background-color:#d9534f;border-color:#d9534f}.btn-success{color:#fff;background-color:#5cb85c;border-color:#5cb85c}.btn-success:hover,.btn-success:focus,.btn-success:active,.btn-success.active{background-color:#4cae4c;border-color:#449d44}.btn-success.disabled,.btn-success[disabled],fieldset[disabled] .btn-success,.btn-success.disabled:hover,.btn-success[disabled]:hover,fieldset[disabled] .btn-success:hover,.btn-success.disabled:focus,.btn-success[disabled]:focus,fieldset[disabled] .btn-success:focus,.btn-success.disabled:active,.btn-success[disabled]:active,fieldset[disabled] .btn-success:active,.btn-success.disabled.active,.btn-success[disabled].active,fieldset[disabled] .btn-success.active{background-color:#5cb85c;border-color:#5cb85c}.btn-info{color:#fff;background-color:#5bc0de;border-color:#5bc0de}.btn-info:hover,.btn-info:focus,.btn-info:active,.btn-info.active{background-color:#46b8da;border-color:#31b0d5}.btn-info.disabled,.btn-info[disabled],fieldset[disabled] .btn-info,.btn-info.disabled:hover,.btn-info[disabled]:hover,fieldset[disabled] .btn-info:hover,.btn-info.disabled:focus,.btn-info[disabled]:focus,fieldset[disabled] .btn-info:focus,.btn-info.disabled:active,.btn-info[disabled]:active,fieldset[disabled] .btn-info:active,.btn-info.disabled.active,.btn-info[disabled].active,fieldset[disabled] .btn-info.active{background-color:#5bc0de;border-color:#5bc0de}.btn-link{font-weight:normal;color:#428bca;cursor:pointer;border-radius:0}.btn-link,.btn-link:active,.btn-link[disabled],fieldset[disabled] .btn-link{background-color:transparent;-webkit-box-shadow:none;box-shadow:none}.btn-link,.btn-link:hover,.btn-link:focus,.btn-link:active{border-color:transparent}.btn-link:hover,.btn-link:focus{color:#2a6496;text-decoration:underline;background-color:transparent}.btn-link[disabled]:hover,fieldset[disabled] .btn-link:hover,.btn-link[disabled]:focus,fieldset[disabled] .btn-link:focus{color:#333;text-decoration:none}.btn-large{padding:14px 16px;font-size:18px;border-radius:6px}.btn-small{padding:5px 10px;font-size:12px;line-height:1.5;border-radius:3px}.btn-block{display:block;width:100%;padding-right:0;padding-left:0}.btn-block+.btn-block{margin-top:5px}input[type="submit"].btn-block,input[type="reset"].btn-block,input[type="button"].btn-block{width:100%}.fade{opacity:0;-webkit-transition:opacity .15s linear;transition:opacity .15s linear}.fade.in{opacity:1}.collapse{display:none}.collapse.in{display:block}.collapsing{position:relative;height:0;overflow:hidden;-webkit-transition:height .35s ease;transition:height .35s ease}.caret{display:inline-block;width:0;height:0;margin-left:2px;vertical-align:middle;border-top:4px solid #000;border-right:4px solid transparent;border-left:4px solid transparent;content:""}.dropdown-menu{position:absolute;top:100%;left:0;z-index:1000;display:none;float:left;min-width:160px;padding:5px 0;margin:2px 0 0;list-style:none;background-color:#fff;border:1px solid #ccc;border:1px solid rgba(0,0,0,0.15);border-radius:4px;-webkit-box-shadow:0 6px 12px rgba(0,0,0,0.175);box-shadow:0 6px 12px rgba(0,0,0,0.175);background-clip:padding-box}.dropdown-menu.pull-right{right:0;left:auto}.dropdown-menu .divider{height:1px;margin:9px 0;overflow:hidden;background-color:#e5e5e5}.dropdown-menu>li>a{display:block;padding:3px 20px;clear:both;font-weight:normal;line-height:1.428571429;color:#333;white-space:nowrap}.dropdown-menu>li>a:hover,.dropdown-menu>li>a:focus{color:#fff;text-decoration:none;background-color:#357ebd;background-image:-webkit-gradient(linear,left 0,left 100%,from(#428bca),to(#357ebd));background-image:-webkit-linear-gradient(top,#428bca,0%,#357ebd,100%);background-image:-moz-linear-gradient(top,#428bca 0,#357ebd 100%);background-image:linear-gradient(to bottom,#428bca 0,#357ebd 100%);background-repeat:repeat-x;filter:progid:DXImageTransform.Microsoft.gradient(startColorstr='#ff428bca',endColorstr='#ff357ebd',GradientType=0)}.dropdown-menu>.active>a,.dropdown-menu>.active>a:hover,.dropdown-menu>.active>a:focus{color:#fff;text-decoration:none;background-color:#357ebd;background-image:-webkit-gradient(linear,left 0,left 100%,from(#428bca),to(#357ebd));background-image:-webkit-linear-gradient(top,#428bca,0%,#357ebd,100%);background-image:-moz-linear-gradient(top,#428bca 0,#357ebd 100%);background-image:linear-gradient(to bottom,#428bca 0,#357ebd 100%);background-repeat:repeat-x;outline:0;filter:progid:DXImageTransform.Microsoft.gradient(startColorstr='#ff428bca',endColorstr='#ff357ebd',GradientType=0)}.dropdown-menu>.disabled>a,.dropdown-menu>.disabled>a:hover,.dropdown-menu>.disabled>a:focus{color:#999}.dropdown-menu>.disabled>a:hover,.dropdown-menu>.disabled>a:focus{text-decoration:none;cursor:not-allowed;background-color:transparent;background-image:none;filter:progid:DXImageTransform.Microsoft.gradient(enabled=false)}.open>.dropdown-menu{display:block}.open>a{outline:0}.dropdown-header{display:block;padding:3px 20px;font-size:12px;line-height:1.428571429;color:#999}.dropdown-backdrop{position:fixed;top:0;right:0;bottom:0;left:0;z-index:990}.pull-right>.dropdown-menu{right:0;left:auto}.dropup .caret,.navbar-fixed-bottom .dropdown .caret{border-top:0;border-bottom:4px solid #000;content:""}.dropup .dropdown-menu,.navbar-fixed-bottom .dropdown .dropdown-menu{top:auto;bottom:100%;margin-bottom:1px}.list-group{padding-left:0;margin-bottom:20px;background-color:#fff}.list-group-item{position:relative;display:block;padding:10px 30px 10px 15px;margin-bottom:-1px;border:1px solid #ddd}.list-group-item:first-child{border-top-right-radius:4px;border-top-left-radius:4px}.list-group-item:last-child{margin-bottom:0;border-bottom-right-radius:4px;border-bottom-left-radius:4px}.list-group-item>.badge{float:right;margin-right:-15px}.list-group-item-heading{margin-top:0;margin-bottom:5px}.list-group-item-text{margin-bottom:0;line-height:1.3}a.list-group-item .list-group-item-heading{color:#333}a.list-group-item .list-group-item-text{color:#555}a.list-group-item:hover,a.list-group-item:focus{text-decoration:none;background-color:#f5f5f5}a.list-group-item.active{z-index:2;color:#fff;background-color:#428bca;border-color:#428bca}a.list-group-item.active .list-group-item-heading{color:inherit}a.list-group-item.active .list-group-item-text{color:#e1edf7}.panel{padding:15px;margin-bottom:20px;background-color:#fff;border:1px solid #ddd;border-radius:4px;-webkit-box-shadow:0 1px 1px rgba(0,0,0,0.05);box-shadow:0 1px 1px rgba(0,0,0,0.05)}.panel-heading{padding:10px 15px;margin:-15px -15px 15px;background-color:#f5f5f5;border-bottom:1px solid #ddd;border-top-right-radius:3px;border-top-left-radius:3px}.panel-title{margin-top:0;margin-bottom:0;font-size:17.5px;font-weight:500}.panel-footer{padding:10px 15px;margin:15px -15px -15px;background-color:#f5f5f5;border-top:1px solid #ddd;border-bottom-right-radius:3px;border-bottom-left-radius:3px}.panel-primary{border-color:#428bca}.panel-primary .panel-heading{color:#fff;background-color:#428bca;border-color:#428bca}.panel-success{border-color:#d6e9c6}.panel-success .panel-heading{color:#468847;background-color:#dff0d8;border-color:#d6e9c6}.panel-warning{border-color:#fbeed5}.panel-warning .panel-heading{color:#c09853;background-color:#fcf8e3;border-color:#fbeed5}.panel-danger{border-color:#eed3d7}.panel-danger .panel-heading{color:#b94a48;background-color:#f2dede;border-color:#eed3d7}.panel-info{border-color:#bce8f1}.panel-info .panel-heading{color:#3a87ad;background-color:#d9edf7;border-color:#bce8f1}.list-group-flush{margin:15px -15px -15px}.list-group-flush .list-group-item{border-width:1px 0}.list-group-flush .list-group-item:first-child{border-top-right-radius:0;border-top-left-radius:0}.list-group-flush .list-group-item:last-child{border-bottom:0}.well{min-height:20px;padding:19px;margin-bottom:20px;background-color:#f5f5f5;border:1px solid #e3e3e3;border-radius:4px;-webkit-box-shadow:inset 0 1px 1px rgba(0,0,0,0.05);box-shadow:inset 0 1px 1px rgba(0,0,0,0.05)}.well blockquote{border-color:#ddd;border-color:rgba(0,0,0,0.15)}.well-large{padding:24px;border-radius:6px}.well-small{padding:9px;border-radius:3px}.close{float:right;font-size:21px;font-weight:bold;line-height:1;color:#000;text-shadow:0 1px 0 #fff;opacity:.2;filter:alpha(opacity=20)}.close:hover,.close:focus{color:#000;text-decoration:none;cursor:pointer;opacity:.5;filter:alpha(opacity=50)}button.close{padding:0;cursor:pointer;background:transparent;border:0;-webkit-appearance:none}.nav{padding-left:0;margin-bottom:0;list-style:none}.nav:before,.nav:after{display:table;content:" "}.nav:after{clear:both}.nav:before,.nav:after{display:table;content:" "}.nav:after{clear:both}.nav>li{position:relative;display:block}.nav>li>a{position:relative;display:block;padding:10px 15px}.nav>li>a:hover,.nav>li>a:focus{text-decoration:none;background-color:#eee}.nav>li.disabled>a{color:#999}.nav>li.disabled>a:hover,.nav>li.disabled>a:focus{color:#999;text-decoration:none;cursor:not-allowed;background-color:transparent}.nav>li+.nav-header{margin-top:9px}.nav.open>a,.nav.open>a:hover,.nav.open>a:focus{color:#fff;background-color:#428bca;border-color:#428bca}.nav.open>a .caret,.nav.open>a:hover .caret,.nav.open>a:focus .caret{border-top-color:#fff;border-bottom-color:#fff}.nav>.pull-right{float:right}.nav .nav-divider{height:1px;margin:9px 0;overflow:hidden;background-color:#e5e5e5}.nav-tabs{border-bottom:1px solid #ddd}.nav-tabs>li{float:left;margin-bottom:-1px}.nav-tabs>li>a{margin-right:2px;line-height:1.428571429;border:1px solid transparent;border-radius:4px 4px 0 0}.nav-tabs>li>a:hover{border-color:#eee}.nav-tabs>li.active>a,.nav-tabs>li.active>a:hover,.nav-tabs>li.active>a:focus{color:#555;cursor:default;background-color:#fff;border:1px solid #ddd;border-bottom-color:transparent}.nav-tabs.nav-justified{width:100%;border-bottom:0}.nav-tabs.nav-justified>li{display:table-cell;float:none;width:1%}.nav-tabs.nav-justified>li>a{text-align:center}.nav-tabs.nav-justified>li>a{margin-right:0;border-bottom:1px solid #ddd}.nav-tabs.nav-justified>.active>a{border-bottom-color:#fff}.nav-pills>li{float:left}.nav-pills>li>a{border-radius:5px}.nav-pills>li+li{margin-left:2px}.nav-pills>li.active>a,.nav-pills>li.active>a:hover,.nav-pills>li.active>a:focus{color:#fff;background-color:#428bca}.nav-stacked>li{float:none}.nav-stacked>li+li>a{margin-top:2px;margin-left:0}.nav-justified{width:100%}.nav-justified>li{display:table-cell;float:none;width:1%}.nav-justified>li>a{text-align:center}.nav-tabs-justified{border-bottom:0}.nav-tabs-justified>li>a{margin-right:0;border-bottom:1px solid #ddd}.nav-tabs-justified>.active>a{border-bottom-color:#fff}.tabbable:before,.tabbable:after{display:table;content:" "}.tabbable:after{clear:both}.tabbable:before,.tabbable:after{display:table;content:" "}.tabbable:after{clear:both}.tab-content>.tab-pane,.pill-content>.pill-pane{display:none}.tab-content>.active,.pill-content>.active{display:block}.nav .caret{border-top-color:#428bca;border-bottom-color:#428bca}.nav a:hover .caret{border-top-color:#2a6496;border-bottom-color:#2a6496}.nav-tabs .dropdown-menu{margin-top:-1px;border-top-right-radius:0;border-top-left-radius:0}.navbar{position:relative;min-height:50px;padding-right:15px;padding-left:15px;margin-bottom:20px;background-color:#eee;border-radius:4px}.navbar:before,.navbar:after{display:table;content:" "}.navbar:after{clear:both}.navbar:before,.navbar:after{display:table;content:" "}.navbar:after{clear:both}.navbar-nav{margin-top:10px;margin-bottom:15px}.navbar-nav>li>a{padding-top:15px;padding-bottom:15px;line-height:20px;color:#777;border-radius:4px}.navbar-nav>li>a:hover,.navbar-nav>li>a:focus{color:#333;background-color:transparent}.navbar-nav>.active>a,.navbar-nav>.active>a:hover,.navbar-nav>.active>a:focus{color:#555;background-color:#d5d5d5}.navbar-nav>.disabled>a,.navbar-nav>.disabled>a:hover,.navbar-nav>.disabled>a:focus{color:#ccc;background-color:transparent}.navbar-nav.pull-right{width:100%}.navbar-static-top{border-radius:0}.navbar-fixed-top,.navbar-fixed-bottom{position:fixed;right:0;left:0;z-index:1030;border-radius:0}.navbar-fixed-top{top:0}.navbar-fixed-bottom{bottom:0;margin-bottom:0}.navbar-brand{display:block;max-width:200px;padding:15px 15px;margin-right:auto;margin-left:auto;font-size:18px;font-weight:500;line-height:20px;color:#777;text-align:center}.navbar-brand:hover,.navbar-brand:focus{color:#5e5e5e;text-decoration:none;background-color:transparent}.navbar-toggle{position:absolute;top:9px;right:10px;width:48px;height:32px;padding:8px 12px;background-color:transparent;border:1px solid #ddd;border-radius:4px}.navbar-toggle:hover,.navbar-toggle:focus{background-color:#ddd}.navbar-toggle .icon-bar{display:block;width:22px;height:2px;background-color:#ccc;border-radius:1px}.navbar-toggle .icon-bar+.icon-bar{margin-top:4px}.navbar-form{margin-top:6px;margin-bottom:6px}.navbar-form .form-control,.navbar-form .radio,.navbar-form .checkbox{display:inline-block}.navbar-form .radio,.navbar-form .checkbox{margin-top:0;margin-bottom:0}.navbar-nav>li>.dropdown-menu{margin-top:0;border-top-right-radius:0;border-top-left-radius:0}.navbar-fixed-bottom .navbar-nav>li>.dropdown-menu{border-bottom-right-radius:0;border-bottom-left-radius:0}.navbar-nav>.dropdown>a:hover .caret,.navbar-nav>.dropdown>a:focus .caret{border-top-color:#333;border-bottom-color:#333}.navbar-nav>.open>a,.navbar-nav>.open>a:hover,.navbar-nav>.open>a:focus{color:#555;background-color:#d5d5d5}.navbar-nav>.open>a .caret,.navbar-nav>.open>a:hover .caret,.navbar-nav>.open>a:focus .caret{border-top-color:#555;border-bottom-color:#555}.navbar-nav>.dropdown>a .caret{border-top-color:#777;border-bottom-color:#777}.navbar-nav.pull-right>li>.dropdown-menu,.navbar-nav>li>.dropdown-menu.pull-right{right:0;left:auto}.navbar-inverse{background-color:#222}.navbar-inverse .navbar-brand{color:#999}.navbar-inverse .navbar-brand:hover,.navbar-inverse .navbar-brand:focus{color:#fff;background-color:transparent}.navbar-inverse .navbar-text{color:#999}.navbar-inverse .navbar-nav>li>a{color:#999}.navbar-inverse .navbar-nav>li>a:hover,.navbar-inverse .navbar-nav>li>a:focus{color:#fff;background-color:transparent}.navbar-inverse .navbar-nav>.active>a,.navbar-inverse .navbar-nav>.active>a:hover,.navbar-inverse .navbar-nav>.active>a:focus{color:#fff;background-color:#080808}.navbar-inverse .navbar-nav>.disabled>a,.navbar-inverse .navbar-nav>.disabled>a:hover,.navbar-inverse .navbar-nav>.disabled>a:focus{color:#444;background-color:transparent}.navbar-inverse .navbar-toggle{border-color:#333}.navbar-inverse .navbar-toggle:hover,.navbar-inverse .navbar-toggle:focus{background-color:#333}.navbar-inverse .navbar-toggle .icon-bar{background-color:#fff}.navbar-inverse .navbar-nav>.open>a,.navbar-inverse .navbar-nav>.open>a:hover,.navbar-inverse .navbar-nav>.open>a:focus{color:#fff;background-color:#080808}.navbar-inverse .navbar-nav>.dropdown>a:hover .caret{border-top-color:#fff;border-bottom-color:#fff}.navbar-inverse .navbar-nav>.dropdown>a .caret{border-top-color:#999;border-bottom-color:#999}.navbar-inverse .navbar-nav>.open>a .caret,.navbar-inverse .navbar-nav>.open>a:hover .caret,.navbar-inverse .navbar-nav>.open>a:focus .caret{border-top-color:#fff;border-bottom-color:#fff}@media screen and (min-width:768px){.navbar-brand{float:left;margin-right:5px;margin-left:-15px}.navbar-nav{float:left;margin-top:0;margin-bottom:0}.navbar-nav>li{float:left}.navbar-nav>li>a{border-radius:0}.navbar-nav.pull-right{float:right;width:auto}.navbar-toggle{position:relative;top:auto;left:auto;display:none}.nav-collapse.collapse{display:block!important;height:auto!important;overflow:visible!important}}.navbar-btn{margin-top:6px}.navbar-text{margin-top:15px;margin-bottom:15px}.navbar-link{color:#777}.navbar-link:hover{color:#333}.navbar-inverse .navbar-link{color:#999}.navbar-inverse .navbar-link:hover{color:#fff}.btn .caret{border-top-color:#fff}.dropup .btn .caret{border-bottom-color:#fff}.btn-group,.btn-group-vertical{position:relative;display:inline-block;vertical-align:middle}.btn-group>.btn,.btn-group-vertical>.btn{position:relative;float:left}.btn-group>.btn:hover,.btn-group-vertical>.btn:hover,.btn-group>.btn:active,.btn-group-vertical>.btn:active{z-index:2}.btn-group .btn+.btn{margin-left:-1px}.btn-toolbar:before,.btn-toolbar:after{display:table;content:" "}.btn-toolbar:after{clear:both}.btn-toolbar:before,.btn-toolbar:after{display:table;content:" "}.btn-toolbar:after{clear:both}.btn-toolbar .btn-group{float:left}.btn-toolbar>.btn+.btn,.btn-toolbar>.btn-group+.btn,.btn-toolbar>.btn+.btn-group,.btn-toolbar>.btn-group+.btn-group{margin-left:5px}.btn-group>.btn:not(:first-child):not(:last-child):not(.dropdown-toggle){border-radius:0}.btn-group>.btn:first-child{margin-left:0}.btn-group>.btn:first-child:not(:last-child):not(.dropdown-toggle){border-top-right-radius:0;border-bottom-right-radius:0}.btn-group>.btn:last-child:not(:first-child),.btn-group>.dropdown-toggle:not(:first-child){border-bottom-left-radius:0;border-top-left-radius:0}.btn-group>.btn-group{float:left}.btn-group>.btn-group:not(:first-child):not(:last-child)>.btn{border-radius:0}.btn-group>.btn-group:first-child>.btn:last-child,.btn-group>.btn-group:first-child>.dropdown-toggle{border-top-right-radius:0;border-bottom-right-radius:0}.btn-group>.btn-group:last-child>.btn:first-child{border-bottom-left-radius:0;border-top-left-radius:0}.btn-group .dropdown-toggle:active,.btn-group.open .dropdown-toggle{outline:0}.btn-group>.btn+.dropdown-toggle{padding-right:8px;padding-left:8px}.btn-group>.btn-large+.dropdown-toggle{padding-right:12px;padding-left:12px}.btn-group.open .dropdown-toggle{-webkit-box-shadow:inset 0 3px 5px rgba(0,0,0,0.125);box-shadow:inset 0 3px 5px rgba(0,0,0,0.125)}.btn .caret{margin-left:0}.btn-large .caret{border-width:5px}.dropup .btn-large .caret{border-bottom-width:5px}.btn-group-vertical>.btn{display:block;float:none;width:100%;max-width:100%}.btn-group-vertical>.btn+.btn{margin-top:-1px}.btn-group-vertical .btn:not(:first-child):not(:last-child){border-radius:0}.btn-group-vertical .btn:first-child{border-bottom-right-radius:0;border-bottom-left-radius:0}.btn-group-vertical .btn:last-child{border-top-right-radius:0;border-top-left-radius:0}.btn-group-justified{display:table;width:100%}.btn-group-justified .btn{display:table-cell;float:none;width:1%}.btn-group[data-toggle="buttons"]>.btn>input[type="radio"],.btn-group[data-toggle="buttons"]>.btn>input[type="checkbox"]{display:none}.breadcrumb{padding:8px 15px;margin-bottom:20px;list-style:none;background-color:#f5f5f5;border-radius:4px}.breadcrumb>li{display:inline-block}.breadcrumb>li+li:before{padding:0 5px;color:#ccc;content:"/\00a0"}.breadcrumb>.active{color:#999}.pagination{display:inline-block;padding-left:0;margin:20px 0;border-radius:4px}.pagination>li{display:inline}.pagination>li>a,.pagination>li>span{float:left;padding:4px 12px;line-height:1.428571429;text-decoration:none;background-color:#fff;border:1px solid #ddd;border-left-width:0}.pagination>li:first-child>a,.pagination>li:first-child>span{border-left-width:1px;border-bottom-left-radius:4px;border-top-left-radius:4px}.pagination>li:last-child>a,.pagination>li:last-child>span{border-top-right-radius:4px;border-bottom-right-radius:4px}.pagination>li>a:hover,.pagination>li>a:focus,.pagination>.active>a,.pagination>.active>span{background-color:#f5f5f5}.pagination>.active>a,.pagination>.active>span{color:#999;cursor:default}.pagination>.disabled>span,.pagination>.disabled>a,.pagination>.disabled>a:hover,.pagination>.disabled>a:focus{color:#999;cursor:not-allowed;background-color:#fff}.pagination-large>li>a,.pagination-large>li>span{padding:14px 16px;font-size:18px}.pagination-large>li:first-child>a,.pagination-large>li:first-child>span{border-bottom-left-radius:6px;border-top-left-radius:6px}.pagination-large>li:last-child>a,.pagination-large>li:last-child>span{border-top-right-radius:6px;border-bottom-right-radius:6px}.pagination-small>li>a,.pagination-small>li>span{padding:5px 10px;font-size:12px}.pagination-small>li:first-child>a,.pagination-small>li:first-child>span{border-bottom-left-radius:3px;border-top-left-radius:3px}.pagination-small>li:last-child>a,.pagination-small>li:last-child>span{border-top-right-radius:3px;border-bottom-right-radius:3px}.pager{padding-left:0;margin:20px 0;text-align:center;list-style:none}.pager:before,.pager:after{display:table;content:" "}.pager:after{clear:both}.pager:before,.pager:after{display:table;content:" "}.pager:after{clear:both}.pager li{display:inline}.pager li>a,.pager li>span{display:inline-block;padding:5px 14px;background-color:#fff;border:1px solid #ddd;border-radius:15px}.pager li>a:hover,.pager li>a:focus{text-decoration:none;background-color:#f5f5f5}.pager .next>a,.pager .next>span{float:right}.pager .previous>a,.pager .previous>span{float:left}.pager .disabled>a,.pager .disabled>a:hover,.pager .disabled>a:focus,.pager .disabled>span{color:#999;cursor:not-allowed;background-color:#fff}.modal-open{overflow:hidden}.modal{position:fixed;top:0;right:0;bottom:0;left:0;z-index:1040;display:none;overflow:auto;overflow-y:scroll}.modal.fade .modal-dialog{-webkit-transform:translate(0,-25%);-ms-transform:translate(0,-25%);transform:translate(0,-25%);-webkit-transition:-webkit-transform .3s ease-out;-moz-transition:-moz-transform .3s ease-out;-o-transition:-o-transform .3s ease-out;transition:transform .3s ease-out}.modal.fade.in .modal-dialog{-webkit-transform:translate(0,0);-ms-transform:translate(0,0);transform:translate(0,0)}.modal-dialog{position:relative;top:0;right:0;left:0;z-index:1050;width:auto;padding:10px}.modal-content{position:relative;background-color:#fff;border:1px solid #999;border:1px solid rgba(0,0,0,0.2);border-radius:6px;outline:0;-webkit-box-shadow:0 3px 9px rgba(0,0,0,0.5);box-shadow:0 3px 9px rgba(0,0,0,0.5);background-clip:padding-box}.modal-backdrop{position:fixed;top:0;right:0;bottom:0;left:0;z-index:1030;background-color:#000}.modal-backdrop.fade{opacity:0;filter:alpha(opacity=0)}.modal-backdrop.fade.in{opacity:.5;filter:alpha(opacity=50)}.modal-header{min-height:16.428571429px;padding:15px;border-bottom:1px solid #e5e5e5}.modal-header .close{margin-top:-2px}.modal-title{margin:0;line-height:1.428571429}.modal-body{position:relative;padding:20px}.modal-footer{padding:19px 20px 20px;margin-top:15px;text-align:right;border-top:1px solid #e5e5e5}.modal-footer:before,.modal-footer:after{display:table;content:" "}.modal-footer:after{clear:both}.modal-footer:before,.modal-footer:after{display:table;content:" "}.modal-footer:after{clear:both}.modal-footer .btn+.btn{margin-bottom:0;margin-left:5px}.modal-footer .btn-group .btn+.btn{margin-left:-1px}.modal-footer .btn-block+.btn-block{margin-left:0}@media screen and (min-width:768px){.modal-dialog{right:auto;left:50%;width:560px;padding-top:30px;padding-bottom:30px;margin-left:-280px}.modal-content{-webkit-box-shadow:0 5px 15px rgba(0,0,0,0.5);box-shadow:0 5px 15px rgba(0,0,0,0.5)}}.tooltip{position:absolute;z-index:1030;display:block;font-size:12px;line-height:1.4;opacity:0;filter:alpha(opacity=0);visibility:visible}.tooltip.in{opacity:1;filter:alpha(opacity=100)}.tooltip.top{padding:5px 0;margin-top:-3px}.tooltip.right{padding:0 5px;margin-left:3px}.tooltip.bottom{padding:5px 0;margin-top:3px}.tooltip.left{padding:0 5px;margin-left:-3px}.tooltip-inner{max-width:200px;padding:3px 8px;color:#fff;text-align:center;text-decoration:none;background-color:rgba(0,0,0,0.9);border-radius:4px}.tooltip-arrow{position:absolute;width:0;height:0;border-color:transparent;border-style:solid}.tooltip.top .tooltip-arrow{bottom:0;left:50%;margin-left:-5px;border-top-color:rgba(0,0,0,0.9);border-width:5px 5px 0}.tooltip.top-left .tooltip-arrow{bottom:0;left:5px;border-top-color:rgba(0,0,0,0.9);border-width:5px 5px 0}.tooltip.top-right .tooltip-arrow{right:5px;bottom:0;border-top-color:rgba(0,0,0,0.9);border-width:5px 5px 0}.tooltip.right .tooltip-arrow{top:50%;left:0;margin-top:-5px;border-right-color:rgba(0,0,0,0.9);border-width:5px 5px 5px 0}.tooltip.left .tooltip-arrow{top:50%;right:0;margin-top:-5px;border-left-color:rgba(0,0,0,0.9);border-width:5px 0 5px 5px}.tooltip.bottom .tooltip-arrow{top:0;left:50%;margin-left:-5px;border-bottom-color:rgba(0,0,0,0.9);border-width:0 5px 5px}.tooltip.bottom-left .tooltip-arrow{top:0;left:5px;border-bottom-color:rgba(0,0,0,0.9);border-width:0 5px 5px}.tooltip.bottom-right .tooltip-arrow{top:0;right:5px;border-bottom-color:rgba(0,0,0,0.9);border-width:0 5px 5px}.popover{position:absolute;top:0;left:0;z-index:1010;display:none;max-width:276px;padding:1px;text-align:left;white-space:normal;background-color:#fff;border:1px solid #ccc;border:1px solid rgba(0,0,0,0.2);border-radius:6px;-webkit-box-shadow:0 5px 10px rgba(0,0,0,0.2);box-shadow:0 5px 10px rgba(0,0,0,0.2);background-clip:padding-box;-webkit-bg-clip:padding-box;-moz-bg-clip:padding}.popover.top{margin-top:-10px}.popover.right{margin-left:10px}.popover.bottom{margin-top:10px}.popover.left{margin-left:-10px}.popover-title{padding:8px 14px;margin:0;font-size:14px;font-weight:normal;line-height:18px;background-color:#f7f7f7;border-bottom:1px solid #ebebeb;border-radius:5px 5px 0 0}.popover-content{padding:9px 14px}.popover .arrow,.popover .arrow:after{position:absolute;display:block;width:0;height:0;border-color:transparent;border-style:solid}.popover .arrow{border-width:11px}.popover .arrow:after{border-width:10px;content:""}.popover.top .arrow{bottom:-11px;left:50%;margin-left:-11px;border-top-color:#999;border-top-color:rgba(0,0,0,0.25);border-bottom-width:0}.popover.top .arrow:after{bottom:1px;margin-left:-10px;border-top-color:#fff;border-bottom-width:0;content:" "}.popover.right .arrow{top:50%;left:-11px;margin-top:-11px;border-right-color:#999;border-right-color:rgba(0,0,0,0.25);border-left-width:0}.popover.right .arrow:after{bottom:-10px;left:1px;border-right-color:#fff;border-left-width:0;content:" "}.popover.bottom .arrow{top:-11px;left:50%;margin-left:-11px;border-bottom-color:#999;border-bottom-color:rgba(0,0,0,0.25);border-top-width:0}.popover.bottom .arrow:after{top:1px;margin-left:-10px;border-bottom-color:#fff;border-top-width:0;content:" "}.popover.left .arrow{top:50%;right:-11px;margin-top:-11px;border-left-color:#999;border-left-color:rgba(0,0,0,0.25);border-right-width:0}.popover.left .arrow:after{right:1px;bottom:-10px;border-left-color:#fff;border-right-width:0;content:" "}.alert{padding:10px 35px 10px 15px;margin-bottom:20px;color:#c09853;background-color:#fcf8e3;border:1px solid #fbeed5;border-radius:4px}.alert h4{margin-top:0;color:inherit}.alert hr{border-top-color:#f8e5be}.alert .alert-link{font-weight:500;color:#a47e3c}.alert .close{position:relative;top:-2px;right:-21px;color:inherit}.alert-success{color:#468847;background-color:#dff0d8;border-color:#d6e9c6}.alert-success hr{border-top-color:#c9e2b3}.alert-success .alert-link{color:#356635}.alert-danger{color:#b94a48;background-color:#f2dede;border-color:#eed3d7}.alert-danger hr{border-top-color:#e6c1c7}.alert-danger .alert-link{color:#953b39}.alert-info{color:#3a87ad;background-color:#d9edf7;border-color:#bce8f1}.alert-info hr{border-top-color:#a6e1ec}.alert-info .alert-link{color:#2d6987}.alert-block{padding-top:15px;padding-bottom:15px}.alert-block>p,.alert-block>ul{margin-bottom:0}.alert-block p+p{margin-top:5px}.thumbnail,.img-thumbnail{padding:4px;line-height:1.428571429;background-color:#fff;border:1px solid #ddd;border-radius:4px;-webkit-transition:all .2s ease-in-out;transition:all .2s ease-in-out}.thumbnail{display:block}.thumbnail>img,.img-thumbnail{display:inline-block;height:auto;max-width:100%}a.thumbnail:hover,a.thumbnail:focus{border-color:#428bca}.thumbnail>img{margin-right:auto;margin-left:auto}.thumbnail .caption{padding:9px;color:#333}.media,.media-body{overflow:hidden;zoom:1}.media,.media .media{margin-top:15px}.media:first-child{margin-top:0}.media-object{display:block}.media-heading{margin:0 0 5px}.media>.pull-left{margin-right:10px}.media>.pull-right{margin-left:10px}.media-list{padding-left:0;list-style:none}.label{display:inline;padding:.25em .6em;font-size:75%;font-weight:500;line-height:1;color:#fff;text-align:center;white-space:nowrap;vertical-align:middle;background-color:#999;border-radius:.25em}.label[href]:hover,.label[href]:focus{color:#fff;text-decoration:none;cursor:pointer;background-color:#808080}.label-danger{background-color:#d9534f}.label-danger[href]:hover,.label-danger[href]:focus{background-color:#c9302c}.label-success{background-color:#5cb85c}.label-success[href]:hover,.label-success[href]:focus{background-color:#449d44}.label-warning{background-color:#f0ad4e}.label-warning[href]:hover,.label-warning[href]:focus{background-color:#ec971f}.label-info{background-color:#5bc0de}.label-info[href]:hover,.label-info[href]:focus{background-color:#31b0d5}.badge{display:inline-block;min-width:10px;padding:3px 7px;font-size:12px;font-weight:bold;line-height:1;color:#fff;text-align:center;white-space:nowrap;vertical-align:middle;background-color:#999;border-radius:10px}.badge:empty{display:none}a.badge:hover,a.badge:focus{color:#fff;text-decoration:none;cursor:pointer}.btn .badge{position:relative;top:-1px}a.list-group-item.active>.badge,.nav-pills>.active>a>.badge{color:#428bca;background-color:#fff}.nav-pills>li>a>.badge{margin-left:3px}@-webkit-keyframes progress-bar-stripes{from{background-position:40px 0}to{background-position:0 0}}@-moz-keyframes progress-bar-stripes{from{background-position:40px 0}to{background-position:0 0}}@-ms-keyframes progress-bar-stripes{from{background-position:40px 0}to{background-position:0 0}}@-o-keyframes progress-bar-stripes{from{background-position:0 0}to{background-position:40px 0}}@keyframes progress-bar-stripes{from{background-position:40px 0}to{background-position:0 0}}.progress{height:20px;margin-bottom:20px;overflow:hidden;background-color:#f5f5f5;border-radius:4px;-webkit-box-shadow:inset 0 1px 2px rgba(0,0,0,0.1);box-shadow:inset 0 1px 2px rgba(0,0,0,0.1)}.progress-bar{float:left;width:0;height:100%;font-size:12px;color:#fff;text-align:center;background-color:#428bca;-webkit-box-shadow:inset 0 -1px 0 rgba(0,0,0,0.15);box-shadow:inset 0 -1px 0 rgba(0,0,0,0.15);-webkit-transition:width .6s ease;transition:width .6s ease}.progress-striped .progress-bar{background-color:#428bca;background-image:-webkit-gradient(linear,0 100%,100% 0,color-stop(0.25,rgba(255,255,255,0.15)),color-stop(0.25,transparent),color-stop(0.5,transparent),color-stop(0.5,rgba(255,255,255,0.15)),color-stop(0.75,rgba(255,255,255,0.15)),color-stop(0.75,transparent),to(transparent));background-image:-webkit-linear-gradient(45deg,rgba(255,255,255,0.15) 25%,transparent 25%,transparent 50%,rgba(255,255,255,0.15) 50%,rgba(255,255,255,0.15) 75%,transparent 75%,transparent);background-image:-moz-linear-gradient(45deg,rgba(255,255,255,0.15) 25%,transparent 25%,transparent 50%,rgba(255,255,255,0.15) 50%,rgba(255,255,255,0.15) 75%,transparent 75%,transparent);background-image:linear-gradient(45deg,rgba(255,255,255,0.15) 25%,transparent 25%,transparent 50%,rgba(255,255,255,0.15) 50%,rgba(255,255,255,0.15) 75%,transparent 75%,transparent);background-size:40px 40px}.progress.active .progress-bar{-webkit-animation:progress-bar-stripes 2s linear infinite;-moz-animation:progress-bar-stripes 2s linear infinite;-ms-animation:progress-bar-stripes 2s linear infinite;-o-animation:progress-bar-stripes 2s linear infinite;animation:progress-bar-stripes 2s linear infinite}.progress-bar-danger{background-color:#d9534f}.progress-striped .progress-bar-danger{background-color:#d9534f;background-image:-webkit-gradient(linear,0 100%,100% 0,color-stop(0.25,rgba(255,255,255,0.15)),color-stop(0.25,transparent),color-stop(0.5,transparent),color-stop(0.5,rgba(255,255,255,0.15)),color-stop(0.75,rgba(255,255,255,0.15)),color-stop(0.75,transparent),to(transparent));background-image:-webkit-linear-gradient(45deg,rgba(255,255,255,0.15) 25%,transparent 25%,transparent 50%,rgba(255,255,255,0.15) 50%,rgba(255,255,255,0.15) 75%,transparent 75%,transparent);background-image:-moz-linear-gradient(45deg,rgba(255,255,255,0.15) 25%,transparent 25%,transparent 50%,rgba(255,255,255,0.15) 50%,rgba(255,255,255,0.15) 75%,transparent 75%,transparent);background-image:linear-gradient(45deg,rgba(255,255,255,0.15) 25%,transparent 25%,transparent 50%,rgba(255,255,255,0.15) 50%,rgba(255,255,255,0.15) 75%,transparent 75%,transparent)}.progress-bar-success{background-color:#5cb85c}.progress-striped .progress-bar-success{background-color:#5cb85c;background-image:-webkit-gradient(linear,0 100%,100% 0,color-stop(0.25,rgba(255,255,255,0.15)),color-stop(0.25,transparent),color-stop(0.5,transparent),color-stop(0.5,rgba(255,255,255,0.15)),color-stop(0.75,rgba(255,255,255,0.15)),color-stop(0.75,transparent),to(transparent));background-image:-webkit-linear-gradient(45deg,rgba(255,255,255,0.15) 25%,transparent 25%,transparent 50%,rgba(255,255,255,0.15) 50%,rgba(255,255,255,0.15) 75%,transparent 75%,transparent);background-image:-moz-linear-gradient(45deg,rgba(255,255,255,0.15) 25%,transparent 25%,transparent 50%,rgba(255,255,255,0.15) 50%,rgba(255,255,255,0.15) 75%,transparent 75%,transparent);background-image:linear-gradient(45deg,rgba(255,255,255,0.15) 25%,transparent 25%,transparent 50%,rgba(255,255,255,0.15) 50%,rgba(255,255,255,0.15) 75%,transparent 75%,transparent)}.progress-bar-warning{background-color:#f0ad4e}.progress-striped .progress-bar-warning{background-color:#f0ad4e;background-image:-webkit-gradient(linear,0 100%,100% 0,color-stop(0.25,rgba(255,255,255,0.15)),color-stop(0.25,transparent),color-stop(0.5,transparent),color-stop(0.5,rgba(255,255,255,0.15)),color-stop(0.75,rgba(255,255,255,0.15)),color-stop(0.75,transparent),to(transparent));background-image:-webkit-linear-gradient(45deg,rgba(255,255,255,0.15) 25%,transparent 25%,transparent 50%,rgba(255,255,255,0.15) 50%,rgba(255,255,255,0.15) 75%,transparent 75%,transparent);background-image:-moz-linear-gradient(45deg,rgba(255,255,255,0.15) 25%,transparent 25%,transparent 50%,rgba(255,255,255,0.15) 50%,rgba(255,255,255,0.15) 75%,transparent 75%,transparent);background-image:linear-gradient(45deg,rgba(255,255,255,0.15) 25%,transparent 25%,transparent 50%,rgba(255,255,255,0.15) 50%,rgba(255,255,255,0.15) 75%,transparent 75%,transparent)}.progress-bar-info{background-color:#5bc0de}.progress-striped .progress-bar-info{background-color:#5bc0de;background-image:-webkit-gradient(linear,0 100%,100% 0,color-stop(0.25,rgba(255,255,255,0.15)),color-stop(0.25,transparent),color-stop(0.5,transparent),color-stop(0.5,rgba(255,255,255,0.15)),color-stop(0.75,rgba(255,255,255,0.15)),color-stop(0.75,transparent),to(transparent));background-image:-webkit-linear-gradient(45deg,rgba(255,255,255,0.15) 25%,transparent 25%,transparent 50%,rgba(255,255,255,0.15) 50%,rgba(255,255,255,0.15) 75%,transparent 75%,transparent);background-image:-moz-linear-gradient(45deg,rgba(255,255,255,0.15) 25%,transparent 25%,transparent 50%,rgba(255,255,255,0.15) 50%,rgba(255,255,255,0.15) 75%,transparent 75%,transparent);background-image:linear-gradient(45deg,rgba(255,255,255,0.15) 25%,transparent 25%,transparent 50%,rgba(255,255,255,0.15) 50%,rgba(255,255,255,0.15) 75%,transparent 75%,transparent)}.accordion{margin-bottom:20px}.accordion-group{margin-bottom:2px;border:1px solid #e5e5e5;border-radius:4px}.accordion-heading{border-bottom:0}.accordion-heading .accordion-toggle{display:block;padding:8px 15px;cursor:pointer}.accordion-inner{padding:9px 15px;border-top:1px solid #e5e5e5}.carousel{position:relative}.carousel-inner{position:relative;width:100%;overflow:hidden}.carousel-inner>.item{position:relative;display:none;-webkit-transition:.6s ease-in-out left;transition:.6s ease-in-out left}.carousel-inner>.item>img,.carousel-inner>.item>a>img{display:inline-block;height:auto;max-width:100%;line-height:1}.carousel-inner>.active,.carousel-inner>.next,.carousel-inner>.prev{display:block}.carousel-inner>.active{left:0}.carousel-inner>.next,.carousel-inner>.prev{position:absolute;top:0;width:100%}.carousel-inner>.next{left:100%}.carousel-inner>.prev{left:-100%}.carousel-inner>.next.left,.carousel-inner>.prev.right{left:0}.carousel-inner>.active.left{left:-100%}.carousel-inner>.active.right{left:100%}.carousel-control{position:absolute;top:0;bottom:0;left:0;width:15%;font-size:20px;color:#fff;text-align:center;text-shadow:0 1px 2px rgba(0,0,0,0.6);opacity:.5;filter:alpha(opacity=50)}.carousel-control.left{background-color:rgba(0,0,0,0.0001);background-color:transparent;background-image:-webkit-gradient(linear,0 top,100% top,from(rgba(0,0,0,0.5)),to(rgba(0,0,0,0.0001)));background-image:-webkit-linear-gradient(left,color-stop(rgba(0,0,0,0.5) 0),color-stop(rgba(0,0,0,0.0001) 100%));background-image:-moz-linear-gradient(left,rgba(0,0,0,0.5) 0,rgba(0,0,0,0.0001) 100%);background-image:linear-gradient(to right,rgba(0,0,0,0.5) 0,rgba(0,0,0,0.0001) 100%);background-repeat:repeat-x;filter:progid:DXImageTransform.Microsoft.gradient(startColorstr='#80000000',endColorstr='#00000000',GradientType=1)}.carousel-control.right{right:0;left:auto;background-color:rgba(0,0,0,0.5);background-color:transparent;background-image:-webkit-gradient(linear,0 top,100% top,from(rgba(0,0,0,0.0001)),to(rgba(0,0,0,0.5)));background-image:-webkit-linear-gradient(left,color-stop(rgba(0,0,0,0.0001) 0),color-stop(rgba(0,0,0,0.5) 100%));background-image:-moz-linear-gradient(left,rgba(0,0,0,0.0001) 0,rgba(0,0,0,0.5) 100%);background-image:linear-gradient(to right,rgba(0,0,0,0.0001) 0,rgba(0,0,0,0.5) 100%);background-repeat:repeat-x;filter:progid:DXImageTransform.Microsoft.gradient(startColorstr='#00000000',endColorstr='#80000000',GradientType=1)}.carousel-control:hover,.carousel-control:focus{color:#fff;text-decoration:none;opacity:.9;filter:alpha(opacity=90)}.carousel-control .glyphicon,.carousel-control .icon-prev,.carousel-control .icon-next{position:absolute;top:50%;left:50%;z-index:5;display:inline-block;width:20px;height:20px;margin-top:-10px;margin-left:-10px;font-family:serif}.carousel-control .icon-prev:before{content:'\2039'}.carousel-control .icon-next:before{content:'\203a'}.carousel-indicators{position:absolute;bottom:10px;left:50%;z-index:15;width:120px;padding-left:0;margin-left:-60px;text-align:center;list-style:none}.carousel-indicators li{display:inline-block;width:10px;height:10px;margin:1px;text-indent:-999px;cursor:pointer;border:1px solid #fff;border-radius:10px}.carousel-indicators .active{width:12px;height:12px;margin:0;background-color:#fff}.carousel-caption{position:absolute;right:15%;bottom:20px;left:15%;z-index:10;padding-top:20px;padding-bottom:20px;color:#fff;text-align:center;text-shadow:0 1px 2px rgba(0,0,0,0.6)}.carousel-caption .btn{text-shadow:none}@media screen and (min-width:768px){.carousel-control .glyphicon,.carousel-control .icon-prev,.carousel-control .icon-next{width:30px;height:30px;margin-top:-15px;margin-left:-15px;font-size:30px}.carousel-caption{right:20%;left:20%;padding-bottom:30px}.carousel-indicators{bottom:20px}}.jumbotron{padding:30px;margin-bottom:30px;font-size:21px;font-weight:200;line-height:2.1428571435;color:inherit;background-color:#eee}.jumbotron h1{line-height:1;color:inherit}.jumbotron p{line-height:1.4}@media screen and (min-width:768px){.jumbotron{padding:50px 60px;border-radius:6px}.jumbotron h1{font-size:63px}}.clearfix:before,.clearfix:after{display:table;content:" "}.clearfix:after{clear:both}.pull-right{float:right}.pull-left{float:left}.hide{display:none!important}.show{display:block!important}.invisible{visibility:hidden}.text-hide{font:0/0 a;color:transparent;text-shadow:none;background-color:transparent;border:0}.affix{position:fixed}@-ms-viewport{width:device-width}@media screen and (max-width:400px){@-ms-viewport{width:320px}}.hidden{display:none!important;visibility:hidden!important}.visible-sm{display:block!important}tr.visible-sm{display:table-row!important}th.visible-sm,td.visible-sm{display:table-cell!important}.visible-md{display:none!important}tr.visible-md{display:none!important}th.visible-md,td.visible-md{display:none!important}.visible-lg{display:none!important}tr.visible-lg{display:none!important}th.visible-lg,td.visible-lg{display:none!important}.hidden-sm{display:none!important}tr.hidden-sm{display:none!important}th.hidden-sm,td.hidden-sm{display:none!important}.hidden-md{display:block!important}tr.hidden-md{display:table-row!important}th.hidden-md,td.hidden-md{display:table-cell!important}.hidden-lg{display:block!important}tr.hidden-lg{display:table-row!important}th.hidden-lg,td.hidden-lg{display:table-cell!important}@media(min-width:768px) and (max-width:991px){.visible-sm{display:none!important}tr.visible-sm{display:none!important}th.visible-sm,td.visible-sm{display:none!important}.visible-md{display:block!important}tr.visible-md{display:table-row!important}th.visible-md,td.visible-md{display:table-cell!important}.visible-lg{display:none!important}tr.visible-lg{display:none!important}th.visible-lg,td.visible-lg{display:none!important}.hidden-sm{display:block!important}tr.hidden-sm{display:table-row!important}th.hidden-sm,td.hidden-sm{display:table-cell!important}.hidden-md{display:none!important}tr.hidden-md{display:none!important}th.hidden-md,td.hidden-md{display:none!important}.hidden-lg{display:block!important}tr.hidden-lg{display:table-row!important}th.hidden-lg,td.hidden-lg{display:table-cell!important}}@media(min-width:992px){.visible-sm{display:none!important}tr.visible-sm{display:none!important}th.visible-sm,td.visible-sm{display:none!important}.visible-md{display:none!important}tr.visible-md{display:none!important}th.visible-md,td.visible-md{display:none!important}.visible-lg{display:block!important}tr.visible-lg{display:table-row!important}th.visible-lg,td.visible-lg{display:table-cell!important}.hidden-sm{display:block!important}tr.hidden-sm{display:table-row!important}th.hidden-sm,td.hidden-sm{display:table-cell!important}.hidden-md{display:block!important}tr.hidden-md{display:table-row!important}th.hidden-md,td.hidden-md{display:table-cell!important}.hidden-lg{display:none!important}tr.hidden-lg{display:none!important}th.hidden-lg,td.hidden-lg{display:none!important}}.visible-print{display:none!important}tr.visible-print{display:none!important}th.visible-print,td.visible-print{display:none!important}@media print{.visible-print{display:block!important}tr.visible-print{display:table-row!important}th.visible-print,td.visible-print{display:table-cell!important}.hidden-print{display:none!important}tr.hidden-print{display:none!important}th.hidden-print,td.hidden-print{display:none!important}}
    </style>

    <!-- zepto -->
    <script type="text/javascript">
/* Zepto v1.1.2 - zepto event ajax form ie - zeptojs.com/license */
var Zepto=function(){function G(a){return a==null?String(a):z[A.call(a)]||"object"}function H(a){return G(a)=="function"}function I(a){return a!=null&&a==a.window}function J(a){return a!=null&&a.nodeType==a.DOCUMENT_NODE}function K(a){return G(a)=="object"}function L(a){return K(a)&&!I(a)&&Object.getPrototypeOf(a)==Object.prototype}function M(a){return a instanceof Array}function N(a){return typeof a.length=="number"}function O(a){return g.call(a,function(a){return a!=null})}function P(a){return a.length>0?c.fn.concat.apply([],a):a}function Q(a){return a.replace(/::/g,"/").replace(/([A-Z]+)([A-Z][a-z])/g,"$1_$2").replace(/([a-z\d])([A-Z])/g,"$1_$2").replace(/_/g,"-").toLowerCase()}function R(a){return a in j?j[a]:j[a]=new RegExp("(^|\\s)"+a+"(\\s|$)")}function S(a,b){return typeof b=="number"&&!k[Q(a)]?b+"px":b}function T(a){var b,c;return i[a]||(b=h.createElement(a),h.body.appendChild(b),c=getComputedStyle(b,"").getPropertyValue("display"),b.parentNode.removeChild(b),c=="none"&&(c="block"),i[a]=c),i[a]}function U(a){return"children"in a?f.call(a.children):c.map(a.childNodes,function(a){if(a.nodeType==1)return a})}function V(c,d,e){for(b in d)e&&(L(d[b])||M(d[b]))?(L(d[b])&&!L(c[b])&&(c[b]={}),M(d[b])&&!M(c[b])&&(c[b]=[]),V(c[b],d[b],e)):d[b]!==a&&(c[b]=d[b])}function W(a,b){return b==null?c(a):c(a).filter(b)}function X(a,b,c,d){return H(b)?b.call(a,c,d):b}function Y(a,b,c){c==null?a.removeAttribute(b):a.setAttribute(b,c)}function Z(b,c){var d=b.className,e=d&&d.baseVal!==a;if(c===a)return e?d.baseVal:d;e?d.baseVal=c:b.className=c}function $(a){var b;try{return a?a=="true"||(a=="false"?!1:a=="null"?null:!/^0/.test(a)&&!isNaN(b=Number(a))?b:/^[\[\{]/.test(a)?c.parseJSON(a):a):a}catch(d){return a}}function _(a,b){b(a);for(var c in a.childNodes)_(a.childNodes[c],b)}var a,b,c,d,e=[],f=e.slice,g=e.filter,h=window.document,i={},j={},k={"column-count":1,columns:1,"font-weight":1,"line-height":1,opacity:1,"z-index":1,zoom:1},l=/^\s*<(\w+|!)[^>]*>/,m=/^<(\w+)\s*\/?>(?:<\/\1>|)$/,n=/<(?!area|br|col|embed|hr|img|input|link|meta|param)(([\w:]+)[^>]*)\/>/ig,o=/^(?:body|html)$/i,p=/([A-Z])/g,q=["val","css","html","text","data","width","height","offset"],r=["after","prepend","before","append"],s=h.createElement("table"),t=h.createElement("tr"),u={tr:h.createElement("tbody"),tbody:s,thead:s,tfoot:s,td:t,th:t,"*":h.createElement("div")},v=/complete|loaded|interactive/,w=/^\.([\w-]+)$/,x=/^#([\w-]*)$/,y=/^[\w-]*$/,z={},A=z.toString,B={},C,D,E=h.createElement("div"),F={tabindex:"tabIndex",readonly:"readOnly","for":"htmlFor","class":"className",maxlength:"maxLength",cellspacing:"cellSpacing",cellpadding:"cellPadding",rowspan:"rowSpan",colspan:"colSpan",usemap:"useMap",frameborder:"frameBorder",contenteditable:"contentEditable"};return B.matches=function(a,b){if(!b||!a||a.nodeType!==1)return!1;var c=a.webkitMatchesSelector||a.mozMatchesSelector||a.oMatchesSelector||a.matchesSelector;if(c)return c.call(a,b);var d,e=a.parentNode,f=!e;return f&&(e=E).appendChild(a),d=~B.qsa(e,b).indexOf(a),f&&E.removeChild(a),d},C=function(a){return a.replace(/-+(.)?/g,function(a,b){return b?b.toUpperCase():""})},D=function(a){return g.call(a,function(b,c){return a.indexOf(b)==c})},B.fragment=function(b,d,e){var g,i,j;return m.test(b)&&(g=c(h.createElement(RegExp.$1))),g||(b.replace&&(b=b.replace(n,"<$1></$2>")),d===a&&(d=l.test(b)&&RegExp.$1),d in u||(d="*"),j=u[d],j.innerHTML=""+b,g=c.each(f.call(j.childNodes),function(){j.removeChild(this)})),L(e)&&(i=c(g),c.each(e,function(a,b){q.indexOf(a)>-1?i[a](b):i.attr(a,b)})),g},B.Z=function(a,b){return a=a||[],a.__proto__=c.fn,a.selector=b||"",a},B.isZ=function(a){return a instanceof B.Z},B.init=function(b,d){var e;if(!b)return B.Z();if(typeof b=="string"){b=b.trim();if(b[0]=="<"&&l.test(b))e=B.fragment(b,RegExp.$1,d),b=null;else{if(d!==a)return c(d).find(b);e=B.qsa(h,b)}}else{if(H(b))return c(h).ready(b);if(B.isZ(b))return b;if(M(b))e=O(b);else if(K(b))e=[b],b=null;else if(l.test(b))e=B.fragment(b.trim(),RegExp.$1,d),b=null;else{if(d!==a)return c(d).find(b);e=B.qsa(h,b)}}return B.Z(e,b)},c=function(a,b){return B.init(a,b)},c.extend=function(a){var b,c=f.call(arguments,1);return typeof a=="boolean"&&(b=a,a=c.shift()),c.forEach(function(c){V(a,c,b)}),a},B.qsa=function(a,b){var c,d=b[0]=="#",e=!d&&b[0]==".",g=d||e?b.slice(1):b,h=y.test(g);return J(a)&&h&&d?(c=a.getElementById(g))?[c]:[]:a.nodeType!==1&&a.nodeType!==9?[]:f.call(h&&!d?e?a.getElementsByClassName(g):a.getElementsByTagName(b):a.querySelectorAll(b))},c.contains=function(a,b){return a!==b&&a.contains(b)},c.type=G,c.isFunction=H,c.isWindow=I,c.isArray=M,c.isPlainObject=L,c.isEmptyObject=function(a){var b;for(b in a)return!1;return!0},c.inArray=function(a,b,c){return e.indexOf.call(b,a,c)},c.camelCase=C,c.trim=function(a){return a==null?"":String.prototype.trim.call(a)},c.uuid=0,c.support={},c.expr={},c.map=function(a,b){var c,d=[],e,f;if(N(a))for(e=0;e<a.length;e++)c=b(a[e],e),c!=null&&d.push(c);else for(f in a)c=b(a[f],f),c!=null&&d.push(c);return P(d)},c.each=function(a,b){var c,d;if(N(a)){for(c=0;c<a.length;c++)if(b.call(a[c],c,a[c])===!1)return a}else for(d in a)if(b.call(a[d],d,a[d])===!1)return a;return a},c.grep=function(a,b){return g.call(a,b)},window.JSON&&(c.parseJSON=JSON.parse),c.each("Boolean Number String Function Array Date RegExp Object Error".split(" "),function(a,b){z["[object "+b+"]"]=b.toLowerCase()}),c.fn={forEach:e.forEach,reduce:e.reduce,push:e.push,sort:e.sort,indexOf:e.indexOf,concat:e.concat,map:function(a){return c(c.map(this,function(b,c){return a.call(b,c,b)}))},slice:function(){return c(f.apply(this,arguments))},ready:function(a){return v.test(h.readyState)&&h.body?a(c):h.addEventListener("DOMContentLoaded",function(){a(c)},!1),this},get:function(b){return b===a?f.call(this):this[b>=0?b:b+this.length]},toArray:function(){return this.get()},size:function(){return this.length},remove:function(){return this.each(function(){this.parentNode!=null&&this.parentNode.removeChild(this)})},each:function(a){return e.every.call(this,function(b,c){return a.call(b,c,b)!==!1}),this},filter:function(a){return H(a)?this.not(this.not(a)):c(g.call(this,function(b){return B.matches(b,a)}))},add:function(a,b){return c(D(this.concat(c(a,b))))},is:function(a){return this.length>0&&B.matches(this[0],a)},not:function(b){var d=[];if(H(b)&&b.call!==a)this.each(function(a){b.call(this,a)||d.push(this)});else{var e=typeof b=="string"?this.filter(b):N(b)&&H(b.item)?f.call(b):c(b);this.forEach(function(a){e.indexOf(a)<0&&d.push(a)})}return c(d)},has:function(a){return this.filter(function(){return K(a)?c.contains(this,a):c(this).find(a).size()})},eq:function(a){return a===-1?this.slice(a):this.slice(a,+a+1)},first:function(){var a=this[0];return a&&!K(a)?a:c(a)},last:function(){var a=this[this.length-1];return a&&!K(a)?a:c(a)},find:function(a){var b,d=this;return typeof a=="object"?b=c(a).filter(function(){var a=this;return e.some.call(d,function(b){return c.contains(b,a)})}):this.length==1?b=c(B.qsa(this[0],a)):b=this.map(function(){return B.qsa(this,a)}),b},closest:function(a,b){var d=this[0],e=!1;typeof a=="object"&&(e=c(a));while(d&&!(e?e.indexOf(d)>=0:B.matches(d,a)))d=d!==b&&!J(d)&&d.parentNode;return c(d)},parents:function(a){var b=[],d=this;while(d.length>0)d=c.map(d,function(a){if((a=a.parentNode)&&!J(a)&&b.indexOf(a)<0)return b.push(a),a});return W(b,a)},parent:function(a){return W(D(this.pluck("parentNode")),a)},children:function(a){return W(this.map(function(){return U(this)}),a)},contents:function(){return this.map(function(){return f.call(this.childNodes)})},siblings:function(a){return W(this.map(function(a,b){return g.call(U(b.parentNode),function(a){return a!==b})}),a)},empty:function(){return this.each(function(){this.innerHTML=""})},pluck:function(a){return c.map(this,function(b){return b[a]})},show:function(){return this.each(function(){this.style.display=="none"&&(this.style.display=""),getComputedStyle(this,"").getPropertyValue("display")=="none"&&(this.style.display=T(this.nodeName))})},replaceWith:function(a){return this.before(a).remove()},wrap:function(a){var b=H(a);if(this[0]&&!b)var d=c(a).get(0),e=d.parentNode||this.length>1;return this.each(function(f){c(this).wrapAll(b?a.call(this,f):e?d.cloneNode(!0):d)})},wrapAll:function(a){if(this[0]){c(this[0]).before(a=c(a));var b;while((b=a.children()).length)a=b.first();c(a).append(this)}return this},wrapInner:function(a){var b=H(a);return this.each(function(d){var e=c(this),f=e.contents(),g=b?a.call(this,d):a;f.length?f.wrapAll(g):e.append(g)})},unwrap:function(){return this.parent().each(function(){c(this).replaceWith(c(this).children())}),this},clone:function(){return this.map(function(){return this.cloneNode(!0)})},hide:function(){return this.css("display","none")},toggle:function(b){return this.each(function(){var d=c(this);(b===a?d.css("display")=="none":b)?d.show():d.hide()})},prev:function(a){return c(this.pluck("previousElementSibling")).filter(a||"*")},next:function(a){return c(this.pluck("nextElementSibling")).filter(a||"*")},html:function(a){return arguments.length===0?this.length>0?this[0].innerHTML:null:this.each(function(b){var d=this.innerHTML;c(this).empty().append(X(this,a,b,d))})},text:function(b){return arguments.length===0?this.length>0?this[0].textContent:null:this.each(function(){this.textContent=b===a?"":""+b})},attr:function(c,d){var e;return typeof c=="string"&&d===a?this.length==0||this[0].nodeType!==1?a:c=="value"&&this[0].nodeName=="INPUT"?this.val():!(e=this[0].getAttribute(c))&&c in this[0]?this[0][c]:e:this.each(function(a){if(this.nodeType!==1)return;if(K(c))for(b in c)Y(this,b,c[b]);else Y(this,c,X(this,d,a,this.getAttribute(c)))})},removeAttr:function(a){return this.each(function(){this.nodeType===1&&Y(this,a)})},prop:function(b,c){return b=F[b]||b,c===a?this[0]&&this[0][b]:this.each(function(a){this[b]=X(this,c,a,this[b])})},data:function(b,c){var d=this.attr("data-"+b.replace(p,"-$1").toLowerCase(),c);return d!==null?$(d):a},val:function(a){return arguments.length===0?this[0]&&(this[0].multiple?c(this[0]).find("option").filter(function(){return this.selected}).pluck("value"):this[0].value):this.each(function(b){this.value=X(this,a,b,this.value)})},offset:function(a){if(a)return this.each(function(b){var d=c(this),e=X(this,a,b,d.offset()),f=d.offsetParent().offset(),g={top:e.top-f.top,left:e.left-f.left};d.css("position")=="static"&&(g.position="relative"),d.css(g)});if(this.length==0)return null;var b=this[0].getBoundingClientRect();return{left:b.left+window.pageXOffset,top:b.top+window.pageYOffset,width:Math.round(b.width),height:Math.round(b.height)}},css:function(a,d){if(arguments.length<2){var e=this[0],f=getComputedStyle(e,"");if(!e)return;if(typeof a=="string")return e.style[C(a)]||f.getPropertyValue(a);if(M(a)){var g={};return c.each(M(a)?a:[a],function(a,b){g[b]=e.style[C(b)]||f.getPropertyValue(b)}),g}}var h="";if(G(a)=="string")!d&&d!==0?this.each(function(){this.style.removeProperty(Q(a))}):h=Q(a)+":"+S(a,d);else for(b in a)!a[b]&&a[b]!==0?this.each(function(){this.style.removeProperty(Q(b))}):h+=Q(b)+":"+S(b,a[b])+";";return this.each(function(){this.style.cssText+=";"+h})},index:function(a){return a?this.indexOf(c(a)[0]):this.parent().children().indexOf(this[0])},hasClass:function(a){return a?e.some.call(this,function(a){return this.test(Z(a))},R(a)):!1},addClass:function(a){return a?this.each(function(b){d=[];var e=Z(this),f=X(this,a,b,e);f.split(/\s+/g).forEach(function(a){c(this).hasClass(a)||d.push(a)},this),d.length&&Z(this,e+(e?" ":"")+d.join(" "))}):this},removeClass:function(b){return this.each(function(c){if(b===a)return Z(this,"");d=Z(this),X(this,b,c,d).split(/\s+/g).forEach(function(a){d=d.replace(R(a)," ")}),Z(this,d.trim())})},toggleClass:function(b,d){return b?this.each(function(e){var f=c(this),g=X(this,b,e,Z(this));g.split(/\s+/g).forEach(function(b){(d===a?!f.hasClass(b):d)?f.addClass(b):f.removeClass(b)})}):this},scrollTop:function(b){if(!this.length)return;var c="scrollTop"in this[0];return b===a?c?this[0].scrollTop:this[0].pageYOffset:this.each(c?function(){this.scrollTop=b}:function(){this.scrollTo(this.scrollX,b)})},scrollLeft:function(b){if(!this.length)return;var c="scrollLeft"in this[0];return b===a?c?this[0].scrollLeft:this[0].pageXOffset:this.each(c?function(){this.scrollLeft=b}:function(){this.scrollTo(b,this.scrollY)})},position:function(){if(!this.length)return;var a=this[0],b=this.offsetParent(),d=this.offset(),e=o.test(b[0].nodeName)?{top:0,left:0}:b.offset();return d.top-=parseFloat(c(a).css("margin-top"))||0,d.left-=parseFloat(c(a).css("margin-left"))||0,e.top+=parseFloat(c(b[0]).css("border-top-width"))||0,e.left+=parseFloat(c(b[0]).css("border-left-width"))||0,{top:d.top-e.top,left:d.left-e.left}},offsetParent:function(){return this.map(function(){var a=this.offsetParent||h.body;while(a&&!o.test(a.nodeName)&&c(a).css("position")=="static")a=a.offsetParent;return a})}},c.fn.detach=c.fn.remove,["width","height"].forEach(function(b){var d=b.replace(/./,function(a){return a[0].toUpperCase()});c.fn[b]=function(e){var f,g=this[0];return e===a?I(g)?g["inner"+d]:J(g)?g.documentElement["scroll"+d]:(f=this.offset())&&f[b]:this.each(function(a){g=c(this),g.css(b,X(this,e,a,g[b]()))})}}),r.forEach(function(a,b){var d=b%2;c.fn[a]=function(){var a,e=c.map(arguments,function(b){return a=G(b),a=="object"||a=="array"||b==null?b:B.fragment(b)}),f,g=this.length>1;return e.length<1?this:this.each(function(a,h){f=d?h:h.parentNode,h=b==0?h.nextSibling:b==1?h.firstChild:b==2?h:null,e.forEach(function(a){if(g)a=a.cloneNode(!0);else if(!f)return c(a).remove();_(f.insertBefore(a,h),function(a){a.nodeName!=null&&a.nodeName.toUpperCase()==="SCRIPT"&&(!a.type||a.type==="text/javascript")&&!a.src&&window.eval.call(window,a.innerHTML)})})})},c.fn[d?a+"To":"insert"+(b?"Before":"After")]=function(b){return c(b)[a](this),this}}),B.Z.prototype=c.fn,B.uniq=D,B.deserializeValue=$,c.zepto=B,c}();window.Zepto=Zepto,window.$===undefined&&(window.$=Zepto),function(a){function m(a){return a._zid||(a._zid=c++)}function n(a,b,c,d){b=o(b);if(b.ns)var e=p(b.ns);return(h[m(a)]||[]).filter(function(a){return a&&(!b.e||a.e==b.e)&&(!b.ns||e.test(a.ns))&&(!c||m(a.fn)===m(c))&&(!d||a.sel==d)})}function o(a){var b=(""+a).split(".");return{e:b[0],ns:b.slice(1).sort().join(" ")}}function p(a){return new RegExp("(?:^| )"+a.replace(" "," .* ?")+"(?: |$)")}function q(a,b){return a.del&&!j&&a.e in k||!!b}function r(a){return l[a]||j&&k[a]||a}function s(b,c,e,f,g,i,j){var k=m(b),n=h[k]||(h[k]=[]);c.split(/\s/).forEach(function(c){if(c=="ready")return a(document).ready(e);var h=o(c);h.fn=e,h.sel=g,h.e in l&&(e=function(b){var c=b.relatedTarget;if(!c||c!==this&&!a.contains(this,c))return h.fn.apply(this,arguments)}),h.del=i;var k=i||e;h.proxy=function(a){a=y(a);if(a.isImmediatePropagationStopped())return;a.data=f;var c=k.apply(b,a._args==d?[a]:[a].concat(a._args));return c===!1&&(a.preventDefault(),a.stopPropagation()),c},h.i=n.length,n.push(h),"addEventListener"in b&&b.addEventListener(r(h.e),h.proxy,q(h,j))})}function t(a,b,c,d,e){var f=m(a);(b||"").split(/\s/).forEach(function(b){n(a,b,c,d).forEach(function(b){delete h[f][b.i],"removeEventListener"in a&&a.removeEventListener(r(b.e),b.proxy,q(b,e))})})}function y(b,c){if(c||!b.isDefaultPrevented){c||(c=b),a.each(x,function(a,d){var e=c[a];b[a]=function(){return this[d]=u,e&&e.apply(c,arguments)},b[d]=v});if(c.defaultPrevented!==d?c.defaultPrevented:"returnValue"in c?c.returnValue===!1:c.getPreventDefault&&c.getPreventDefault())b.isDefaultPrevented=u}return b}function z(a){var b,c={originalEvent:a};for(b in a)!w.test(b)&&a[b]!==d&&(c[b]=a[b]);return y(c,a)}var b=a.zepto.qsa,c=1,d,e=Array.prototype.slice,f=a.isFunction,g=function(a){return typeof a=="string"},h={},i={},j="onfocusin"in window,k={focus:"focusin",blur:"focusout"},l={mouseenter:"mouseover",mouseleave:"mouseout"};i.click=i.mousedown=i.mouseup=i.mousemove="MouseEvents",a.event={add:s,remove:t},a.proxy=function(b,c){if(f(b)){var d=function(){return b.apply(c,arguments)};return d._zid=m(b),d}if(g(c))return a.proxy(b[c],b);throw new TypeError("expected function")},a.fn.bind=function(a,b,c){return this.on(a,b,c)},a.fn.unbind=function(a,b){return this.off(a,b)},a.fn.one=function(a,b,c,d){return this.on(a,b,c,d,1)};var u=function(){return!0},v=function(){return!1},w=/^([A-Z]|returnValue$|layer[XY]$)/,x={preventDefault:"isDefaultPrevented",stopImmediatePropagation:"isImmediatePropagationStopped",stopPropagation:"isPropagationStopped"};a.fn.delegate=function(a,b,c){return this.on(b,a,c)},a.fn.undelegate=function(a,b,c){return this.off(b,a,c)},a.fn.live=function(b,c){return a(document.body).delegate(this.selector,b,c),this},a.fn.die=function(b,c){return a(document.body).undelegate(this.selector,b,c),this},a.fn.on=function(b,c,h,i,j){var k,l,m=this;if(b&&!g(b))return a.each(b,function(a,b){m.on(a,c,h,b,j)}),m;!g(c)&&!f(i)&&i!==!1&&(i=h,h=c,c=d);if(f(h)||h===!1)i=h,h=d;return i===!1&&(i=v),m.each(function(d,f){j&&(k=function(a){return t(f,a.type,i),i.apply(this,arguments)}),c&&(l=function(b){var d,g=a(b.target).closest(c,f).get(0);if(g&&g!==f)return d=a.extend(z(b),{currentTarget:g,liveFired:f}),(k||i).apply(g,[d].concat(e.call(arguments,1)))}),s(f,b,i,h,c,l||k)})},a.fn.off=function(b,c,e){var h=this;return b&&!g(b)?(a.each(b,function(a,b){h.off(a,c,b)}),h):(!g(c)&&!f(e)&&e!==!1&&(e=c,c=d),e===!1&&(e=v),h.each(function(){t(this,b,e,c)}))},a.fn.trigger=function(b,c){return b=g(b)||a.isPlainObject(b)?a.Event(b):y(b),b._args=c,this.each(function(){"dispatchEvent"in this?this.dispatchEvent(b):a(this).triggerHandler(b,c)})},a.fn.triggerHandler=function(b,c){var d,e;return this.each(function(f,h){d=z(g(b)?a.Event(b):b),d._args=c,d.target=h,a.each(n(h,b.type||b),function(a,b){e=b.proxy(d);if(d.isImmediatePropagationStopped())return!1})}),e},"focusin focusout load resize scroll unload click dblclick mousedown mouseup mousemove mouseover mouseout mouseenter mouseleave change select keydown keypress keyup error".split(" ").forEach(function(b){a.fn[b]=function(a){return a?this.bind(b,a):this.trigger(b)}}),["focus","blur"].forEach(function(b){a.fn[b]=function(a){return a?this.bind(b,a):this.each(function(){try{this[b]()}catch(a){}}),this}}),a.Event=function(a,b){g(a)||(b=a,a=b.type);var c=document.createEvent(i[a]||"Events"),d=!0;if(b)for(var e in b)e=="bubbles"?d=!!b[e]:c[e]=b[e];return c.initEvent(a,d,!0),y(c)}}(Zepto),function($){function triggerAndReturn(a,b,c){var d=$.Event(b);return $(a).trigger(d,c),!d.isDefaultPrevented()}function triggerGlobal(a,b,c,d){if(a.global)return triggerAndReturn(b||document,c,d)}function ajaxStart(a){a.global&&$.active++===0&&triggerGlobal(a,null,"ajaxStart")}function ajaxStop(a){a.global&&!--$.active&&triggerGlobal(a,null,"ajaxStop")}function ajaxBeforeSend(a,b){var c=b.context;if(b.beforeSend.call(c,a,b)===!1||triggerGlobal(b,c,"ajaxBeforeSend",[a,b])===!1)return!1;triggerGlobal(b,c,"ajaxSend",[a,b])}function ajaxSuccess(a,b,c,d){var e=c.context,f="success";c.success.call(e,a,f,b),d&&d.resolveWith(e,[a,f,b]),triggerGlobal(c,e,"ajaxSuccess",[b,c,a]),ajaxComplete(f,b,c)}function ajaxError(a,b,c,d,e){var f=d.context;d.error.call(f,c,b,a),e&&e.rejectWith(f,[c,b,a]),triggerGlobal(d,f,"ajaxError",[c,d,a||b]),ajaxComplete(b,c,d)}function ajaxComplete(a,b,c){var d=c.context;c.complete.call(d,b,a),triggerGlobal(c,d,"ajaxComplete",[b,c]),ajaxStop(c)}function empty(){}function mimeToDataType(a){return a&&(a=a.split(";",2)[0]),a&&(a==htmlType?"html":a==jsonType?"json":scriptTypeRE.test(a)?"script":xmlTypeRE.test(a)&&"xml")||"text"}function appendQuery(a,b){return b==""?a:(a+"&"+b).replace(/[&?]{1,2}/,"?")}function serializeData(a){a.processData&&a.data&&$.type(a.data)!="string"&&(a.data=$.param(a.data,a.traditional)),a.data&&(!a.type||a.type.toUpperCase()=="GET")&&(a.url=appendQuery(a.url,a.data),a.data=undefined)}function parseArguments(a,b,c,d){var e=!$.isFunction(b);return{url:a,data:e?b:undefined,success:e?$.isFunction(c)?c:undefined:b,dataType:e?d||c:c}}function serialize(a,b,c,d){var e,f=$.isArray(b),g=$.isPlainObject(b);$.each(b,function(b,h){e=$.type(h),d&&(b=c?d:d+"["+(g||e=="object"||e=="array"?b:"")+"]"),!d&&f?a.add(h.name,h.value):e=="array"||!c&&e=="object"?serialize(a,h,c,b):a.add(b,h)})}var jsonpID=0,document=window.document,key,name,rscript=/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,scriptTypeRE=/^(?:text|application)\/javascript/i,xmlTypeRE=/^(?:text|application)\/xml/i,jsonType="application/json",htmlType="text/html",blankRE=/^\s*$/;$.active=0,$.ajaxJSONP=function(a,b){if("type"in a){var c=a.jsonpCallback,d=($.isFunction(c)?c():c)||"jsonp"+ ++jsonpID,e=document.createElement("script"),f=window[d],g,h=function(a){$(e).triggerHandler("error",a||"abort")},i={abort:h},j;return b&&b.promise(i),$(e).on("load error",function(c,h){clearTimeout(j),$(e).off().remove(),c.type=="error"||!g?ajaxError(null,h||"error",i,a,b):ajaxSuccess(g[0],i,a,b),window[d]=f,g&&$.isFunction(f)&&f(g[0]),f=g=undefined}),ajaxBeforeSend(i,a)===!1?(h("abort"),i):(window[d]=function(){g=arguments},e.src=a.url.replace(/=\?/,"="+d),document.head.appendChild(e),a.timeout>0&&(j=setTimeout(function(){h("timeout")},a.timeout)),i)}return $.ajax(a)},$.ajaxSettings={type:"GET",beforeSend:empty,success:empty,error:empty,complete:empty,context:null,global:!0,xhr:function(){return new window.XMLHttpRequest},accepts:{script:"text/javascript, application/javascript, application/x-javascript",json:jsonType,xml:"application/xml, text/xml",html:htmlType,text:"text/plain"},crossDomain:!1,timeout:0,processData:!0,cache:!0},$.ajax=function(options){var settings=$.extend({},options||{}),deferred=$.Deferred&&$.Deferred();for(key in $.ajaxSettings)settings[key]===undefined&&(settings[key]=$.ajaxSettings[key]);ajaxStart(settings),settings.crossDomain||(settings.crossDomain=/^([\w-]+:)?\/\/([^\/]+)/.test(settings.url)&&RegExp.$2!=window.location.host),settings.url||(settings.url=window.location.toString()),serializeData(settings),settings.cache===!1&&(settings.url=appendQuery(settings.url,"_="+Date.now()));var dataType=settings.dataType,hasPlaceholder=/=\?/.test(settings.url);if(dataType=="jsonp"||hasPlaceholder)return hasPlaceholder||(settings.url=appendQuery(settings.url,settings.jsonp?settings.jsonp+"=?":settings.jsonp===!1?"":"callback=?")),$.ajaxJSONP(settings,deferred);var mime=settings.accepts[dataType],headers={},setHeader=function(a,b){headers[a.toLowerCase()]=[a,b]},protocol=/^([\w-]+:)\/\//.test(settings.url)?RegExp.$1:window.location.protocol,xhr=settings.xhr(),nativeSetHeader=xhr.setRequestHeader,abortTimeout;deferred&&deferred.promise(xhr),settings.crossDomain||setHeader("X-Requested-With","XMLHttpRequest"),setHeader("Accept",mime||"*/*");if(mime=settings.mimeType||mime)mime.indexOf(",")>-1&&(mime=mime.split(",",2)[0]),xhr.overrideMimeType&&xhr.overrideMimeType(mime);(settings.contentType||settings.contentType!==!1&&settings.data&&settings.type.toUpperCase()!="GET")&&setHeader("Content-Type",settings.contentType||"application/x-www-form-urlencoded");if(settings.headers)for(name in settings.headers)setHeader(name,settings.headers[name]);xhr.setRequestHeader=setHeader,xhr.onreadystatechange=function(){if(xhr.readyState==4){xhr.onreadystatechange=empty,clearTimeout(abortTimeout);var result,error=!1;if(xhr.status>=200&&xhr.status<300||xhr.status==304||xhr.status==0&&protocol=="file:"){dataType=dataType||mimeToDataType(settings.mimeType||xhr.getResponseHeader("content-type")),result=xhr.responseText;try{dataType=="script"?(1,eval)(result):dataType=="xml"?result=xhr.responseXML:dataType=="json"&&(result=blankRE.test(result)?null:$.parseJSON(result))}catch(e){error=e}error?ajaxError(error,"parsererror",xhr,settings,deferred):ajaxSuccess(result,xhr,settings,deferred)}else ajaxError(xhr.statusText||null,xhr.status?"error":"abort",xhr,settings,deferred)}};if(ajaxBeforeSend(xhr,settings)===!1)return xhr.abort(),ajaxError(null,"abort",xhr,settings,deferred),xhr;if(settings.xhrFields)for(name in settings.xhrFields)xhr[name]=settings.xhrFields[name];var async="async"in settings?settings.async:!0;xhr.open(settings.type,settings.url,async,settings.username,settings.password);for(name in headers)nativeSetHeader.apply(xhr,headers[name]);return settings.timeout>0&&(abortTimeout=setTimeout(function(){xhr.onreadystatechange=empty,xhr.abort(),ajaxError(null,"timeout",xhr,settings,deferred)},settings.timeout)),xhr.send(settings.data?settings.data:null),xhr},$.get=function(a,b,c,d){return $.ajax(parseArguments.apply(null,arguments))},$.post=function(a,b,c,d){var e=parseArguments.apply(null,arguments);return e.type="POST",$.ajax(e)},$.getJSON=function(a,b,c){var d=parseArguments.apply(null,arguments);return d.dataType="json",$.ajax(d)},$.fn.load=function(a,b,c){if(!this.length)return this;var d=this,e=a.split(/\s/),f,g=parseArguments(a,b,c),h=g.success;return e.length>1&&(g.url=e[0],f=e[1]),g.success=function(a){d.html(f?$("<div>").html(a.replace(rscript,"")).find(f):a),h&&h.apply(d,arguments)},$.ajax(g),this};var escape=encodeURIComponent;$.param=function(a,b){var c=[];return c.add=function(a,b){this.push(escape(a)+"="+escape(b))},serialize(c,a,b),c.join("&").replace(/%20/g,"+")}}(Zepto),function(a){a.fn.serializeArray=function(){var b=[],c;return a([].slice.call(this.get(0).elements)).each(function(){c=a(this);var d=c.attr("type");this.nodeName.toLowerCase()!="fieldset"&&!this.disabled&&d!="submit"&&d!="reset"&&d!="button"&&(d!="radio"&&d!="checkbox"||this.checked)&&b.push({name:c.attr("name"),value:c.val()})}),b},a.fn.serialize=function(){var a=[];return this.serializeArray().forEach(function(b){a.push(encodeURIComponent(b.name)+"="+encodeURIComponent(b.value))}),a.join("&")},a.fn.submit=function(b){if(b)this.bind("submit",b);else if(this.length){var c=a.Event("submit");this.eq(0).trigger(c),c.isDefaultPrevented()||this.get(0).submit()}return this}}(Zepto),function(a){"__proto__"in{}||a.extend(a.zepto,{Z:function(b,c){return b=b||[],a.extend(b,a.fn),b.selector=c||"",b.__Z=!0,b},isZ:function(b){return a.type(b)==="array"&&"__Z"in b}});try{getComputedStyle(undefined)}catch(b){var c=getComputedStyle;window.getComputedStyle=function(a){try{return c(a)}catch(b){return null}}}}(Zepto)
    </script>

    <style type="text/css">
        body {
            background: #F9F9F9;
            font-size: 14px;
            line-height: 22px;
            font-family: Helvetica Neue, Helvetica, Arial;
        }

        a {
            color: #000;
            text-decoration: underline;
        }

        li ul, li ol{
            margin: 0;
        }

        .anchor {
            cursor: pointer;
        }
        .anchor .anchor_char{
            visibility: hidden;
            padding-left: 0.2em;
            font-size: 0.9em;
            opacity: 0.5;
        }
        .anchor:hover .anchor_char{
            visibility: visible;
        }

        .sidebar{
            background: #FFF;
            position: fixed;
            z-index: 10;
            top: 0;
            left: 0;
            bottom: 0;
            width: 230px;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 15px 0 30px 30px;
            border-right: 1px solid #bbb;
            font-family: "Lucida Grande", "Lucida Sans Unicode", Helvetica, Arial, sans-serif !important;
        }

        .sidebar ul{
            margin: 0;
            list-style: none;
            padding: 0;
        }

        .sidebar ul a:hover {
            text-decoration: underline;
            color: #333;
        }

        .sidebar > ul > li {
            margin-top: 15px;
        }

        .sidebar > ul > li > a {
            font-weight: bold;
        }

        .sidebar ul ul {
            margin-top: 5px;
            font-size: 11px;
            line-height: 14px;
        }

        .sidebar ul ul li:before {
            content: "- "; 
        }
        .sidebar ul ul li {
            margin-bottom: 3px;
        }
        .sidebar ul ul li a {
            text-decoration: none;
        }

        .toggle_sidebar_button{
            display: none;
            position: fixed;
            z-index: 11;
            top: 0;
            width: 44px;
            height: 44px;
            background: #000;
            background: rgba(0,0,0,0.7);
            margin-left: 230px;
        }
        .toggle_sidebar_button:hover {
            background: rgba(0,0,0,1);
            cursor: pointer;
        }
            .toggle_sidebar_button .line{
                height: 2px;
                width: 21px;
                margin-left: 11px;
                margin-top: 5px;
                background: #FFF;
            }
            .toggle_sidebar_button .line:first-child {
                margin-top: 15px;
            }

        .main_container {
            width: 100%;
            padding-left: 260px;
            margin: 30px;
            margin-left: 0px;
            padding-right: 30px;
        }

        .main_container p, ul{
            margin: 25px 0;
        }

        .main_container ul {
            list-style: circle;
            font-size: 13px;
            line-height: 18px;
            padding-left: 15px;
        }        

        pre {
            font-size: 12px;
            border: 4px solid #bbb;
            border-top: 0;
            border-bottom: 0;
            margin: 0px 0 25px;
            padding-top: 0px;
            padding-bottom: 0px;

            font-family: Monaco, Consolas, "Lucida Console", monospace;
            line-height: 18px;
            font-style: normal;
            background: none;
            border-radius: 0px;
            overflow-x: scroll;

            word-wrap: normal;
            white-space: pre;
        }

        .main_container {
            width: 840px;
        }

        .main_container p, ul, pre {
            width: 100%;
        }

        code {
            padding: 0px 3px;
            color: #333;
            background: #fff;
            border: 1px solid #ddd;
            zoom: 1;
            white-space: nowrap;
            border-radius: 0;
            font-family: Monaco, Consolas, "Lucida Console", monospace;
            font-size: 12px;
            line-height: 18px;
            font-style: normal;
        }

        em {
            font-size: 12px;
            line-height: 18px;
        }

        @media (max-width: 820px) {
            .sidebar {
                display: none;
            }

            .main_container {
                padding: 0px;
                width: 100%;
            }

            .main_container > *{
                padding-left: 10px;
                padding-right: 10px;
            }
            .main_container > ul, 
            .main_container > ol {
                padding-left: 27px;
            }
            .force_show_sidebar .main_container {
                display: none;
            }
            .force_show_sidebar .sidebar {
                width: 100%;
            }
            .force_show_sidebar .sidebar a{
                font-size: 1.5em;
                line-height: 1.5em;
            }
            .force_show_sidebar .toggle_sidebar_button {
                right: 0;
            }
            .force_show_sidebar .toggle_sidebar_button .line:first-child, 
            .force_show_sidebar .toggle_sidebar_button .line:last-child {
                visibility: hidden;
            }

            .toggle_sidebar_button {
                margin-left: 0px;
                display: block;
            }

            pre {
                font-size: 12px;
                border: 1px solid #bbb;
                border-left: 0;
                border-right: 0;
                padding: 9px;
                background: #FFF;
            }

            code {
                word-wrap: break-word;
                white-space: normal;
            }
        }

        .force_show_sidebar .sidebar {
            display: block;
        }

        .force_show_sidebar .main_container {
            padding-left: 260px;
        }

        .force_show_sidebar .toggle_sidebar_button{
            margin-left: 230px;
        }
    </style>

    <script type="text/javascript">
        $(function(){
            $('.toggle_sidebar_button').on('click', function(){
                $('body').toggleClass('force_show_sidebar');
            });

            // hide sidebar on every click in menu (if small screen)
            $('.sidebar').find('a').on('click', function(){
                $('body').removeClass('force_show_sidebar');
            });

            // add anchors
            $.each($('.main_container').find('h1,h2,h3,h4,h5,h6'), function(key, item){
                if ($(item).attr('id')) {
                    $(item).addClass('anchor');
                    $(item).append($('<span class="anchor_char">¶</span>'))
                    $(item).on('click', function(){
                        window.location = '#' + $(item).attr('id');
                    })
                }
            });

            // remove <code> tag inside of <pre>
            $.each($('pre > code'), function(key, item){
                $(item).parent().html($(item).html())
            })
        })
    </script>
</head>
<body>
    <a class="toggle_sidebar_button">
        <div class="line"></div>
        <div class="line"></div>
        <div class="line"></div>
    </a>
    <div class="sidebar">
        <!-- toc -->
    </div>
    <div class="main_container">
        <!-- main_content -->
    </div>
</body>
</html>'''


def force_text(text):
    if isinstance(text, unicode):
        return text
    else:
        return text.decode('utf-8')


class BackDoc:
    def __init__(self, markdown_converter, template_html, stdin, stdout):
        self.markdown_converter = markdown_converter
        self.template_html = force_text(template_html)
        self.stdin = stdin
        self.stdout = stdout
        self.parser = self.get_parser()

    def run(self, argv):
        kwargs = self.get_kwargs(argv)
        self.stdout.write(self.get_result_html(**kwargs))

    def get_kwargs(self, argv):
        parsed = dict(self.parser.parse_args(argv)._get_kwargs())
        return self.prepare_kwargs_from_parsed_data(parsed)

    def prepare_kwargs_from_parsed_data(self, parsed):
        kwargs = {}
        kwargs['title'] = force_text(parsed.get('title') or 'Documentation')
        if parsed.get('source'):
            kwargs['markdown_src'] = open(parsed['source'], 'r').read()
        else:
            kwargs['markdown_src'] = self.stdin.read()
        kwargs['markdown_src'] = force_text(kwargs['markdown_src'] or '')
        return kwargs

    def get_result_html(self, title, markdown_src):
        response = self.get_converted_to_html_response(markdown_src)
        return (
            self.template_html.replace('<!-- title -->', title)
                              .replace('<!-- toc -->', response.toc_html and force_text(response.toc_html) or '')
                              .replace('<!-- main_content -->', force_text(response))
        )

    def get_converted_to_html_response(self, markdown_src):
        return self.markdown_converter.convert(markdown_src)

    def get_parser(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-t',
            '--title',
            help='Documentation title header',
            required=False,
        )
        parser.add_argument(
            '-s',
            '--source',
            help='Markdown source file path',
            required=False,
        )
        return parser


if __name__ == '__main__':
    BackDoc(
        markdown_converter=Markdown(extras=['toc']), 
        template_html=template_html,
        stdin=sys.stdin,
        stdout=sys.stdout
    ).run(argv=sys.argv[1:])
