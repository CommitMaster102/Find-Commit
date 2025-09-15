<h1>API: <code>fuzzy</code></h1>

<p>Module: <code>find_commits_lib.fuzzy</code></p>

<h2>Tokenization &amp; Shingles</h2>
<ul>
  <li><code>tokenize_for_fuzzy(text) -&gt; list[str]</code></li>
  <li><code>shingle_tokens(tokens, k=5) -&gt; list[str]</code></li>
  <li><code>fingerprint_text_for_fuzzy(text, k=5) -&gt; set[str]</code></li>
  
</ul>

<h2>Jaccard</h2>
<ul>
  <li><code>jaccard_similarity(a, b) -&gt; float</code></li>
  
</ul>

<h2>MinHash</h2>
<ul>
  <li><code>minhash_signature(shingles, num_perm=128) -&gt; list[int]</code></li>
  <li><code>minhash_similarity(sig_a, sig_b) -&gt; float</code></li>
  
</ul>

<h2>SimHash</h2>
<ul>
  <li><code>simhash64(text) -&gt; int</code></li>
  <li><code>simhash_similarity(a, b) -&gt; float</code></li>
  
</ul>

<h2>Character n‑grams &amp; Winnowing</h2>
<ul>
  <li><code>char_ngram_set(text, n=5) -&gt; set[str]</code></li>
  <li><code>winnow_fingerprint(text, k=5, window=4) -&gt; set[str]</code></li>
  
</ul>

<h2>Notes</h2>
<ul>
  <li>Tokenization applies NFKC normalization, lowercases, and splits identifiers into meaningful parts (snake/camel/acronyms/digits).</li>
  <li><code>simhash64_from_tokens(tokens) -&gt; int</code> is available if you need direct token control.</li>
  
</ul>
