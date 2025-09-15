import pytest

from find_commits_lib.fuzzy import shingle_tokens, tokenize_for_fuzzy


class TestTokenizeForFuzzy:
    """Thorough, parameterized coverage of identifier and Unicode handling."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            (
                "HTTPRequest2ID_manager",
                ["http", "request", "2", "id", "manager"],
            ),
            (
                "snake_caseNameXML42",
                ["snake", "case", "name", "xml", "42"],
            ),
            ("version2update10", ["version", "2", "update", "10"]),
            ("__init__", ["init"]),
            ("___HTTP___", ["http"]),
            # Acronym grouping rules
            ("XMLHTTPRequest", ["xmlhttp", "request"]),
            ("parseXMLID", ["parse", "xmlid"]),
            # Mixed alphanumerics
            ("file2Version10", ["file", "2", "version", "10"]),
            ("deadBEEF1234", ["dead", "beef", "1234"]),
            # Punctuation and separators
            ("kebab-case", ["kebab", "case"]),
            ("HTTP-Request_ID2", ["http", "request", "id", "2"]),
            (".-+/*", []),
            # Dotted module/class paths
            ("my.module.ClassName", ["my", "module", "class", "name"]),
            # Small and boundary cases
            ("", []),
            ("__", []),
            ("aB", ["a", "b"]),
            ("12345", ["12345"]),
            ("   \t\n", []),
            # Underscore collapsing
            ("a__b___c", ["a", "b", "c"]),
            ("ver_2_beta_10", ["ver", "2", "beta", "10"]),
            # Camel + numbers
            ("JSON2XML", ["json", "2", "xml"]),
            ("APIResponse", ["api", "response"]),
            ("A", ["a"]),
        ],
    )
    def test_ascii_and_identifier_styles(self, text, expected):
        assert tokenize_for_fuzzy(text) == expected

    @pytest.mark.parametrize(
        "text,expected",
        [
            # Full-width Latin letters -> ASCII via NFKC
            ("ＦｏｏＢａｒ", ["foo", "bar"]),
            # Full-width letters + digits
            ("ＡＢＣ１２３def", ["abc", "123", "def"]),
            # Diacritics and combining accents split tokens
            ("naïveXML", ["na", "ve", "xml"]),
            ("Cafe\u0301XML", ["caf", "xml"]),
            # Non‑Latin scripts are ignored; mixed content keeps ASCII parts
            ("变量名", []),
            ("τεστ", []),
            ("Привет", []),
            ("变量varName", ["var", "name"]),
            # Punctuation like em‑dash separates
            ("foo—bar", ["foo", "bar"]),
        ],
    )
    def test_unicode_normalization_and_non_ascii(self, text, expected):
        assert tokenize_for_fuzzy(text) == expected


class TestShingleTokens:
    @pytest.mark.parametrize(
        "tokens,k,expected",
        [
            (["a", "b", "c"], 1, ["a", "b", "c"]),
            (["a", "b", "c"], 0, ["a", "b", "c"]),
            (["a", "b", "c"], -2, ["a", "b", "c"]),
            (["a", "b", "c"], 2, ["a b", "b c"]),
            (["a", "b", "c"], 3, ["a b c"]),
            (["a", "b", "c"], 4, ["a b c"]),
            (["a", "b"], 5, ["a b"]),
            (["only"], 5, ["only"]),
            ([], 3, []),
        ],
    )
    def test_shingle_behavior(self, tokens, k, expected):
        assert shingle_tokens(tokens, k) == expected
