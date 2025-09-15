<h1>🧠 Similarity Modes</h1>

<p>
  When no exact blob is found, Find‑Commit scans commits touching candidate paths and scores them using the selected similarity. Thresholds include only sufficiently similar candidates.
</p>

<h2>Global Parameters</h2>
<ul>
  <li><code>--similarity-threshold FLOAT</code>: keep candidates with score <code>&ge;</code> threshold. Default: <code>0.92</code>.</li>
  <li>Tokenization: text is normalized to NFKC, lower‑cased, and split into identifier‑aware tokens (snake_case, camelCase, acronyms, digits). Non‑ASCII scripts are ignored; mixed content keeps ASCII segments.</li>
  
</ul>

<hr>

<h2>1) Jaccard (default)</h2>
<p><strong>What it does</strong>: Converts the file to tokens, forms contiguous <em>k</em>-shingles, and computes Jaccard similarity between the sets: <code>|A ∩ B| / |A ∪ B|</code>.</p>
<ul>
  <li><strong>Parameters</strong>: <code>--shingle-size k</code> (default 5)</li>
  <li><strong>Complexity</strong>: O(|A| + |B|) set operations after shingling</li>
  <li><strong>Strengths</strong>: Simple, deterministic, robust to minor token reorderings at window size.</li>
  <li><strong>Limitations</strong>: Sensitive to large reorderings or insertion bursts; set size can grow for long files.</li>
  <li><strong>Use when</strong>: You want exact set overlap accuracy and the files aren’t extremely large.</li>
  <li><strong>Example</strong>:
    <pre><code>--similarity-mode jaccard --shingle-size 5 --similarity-threshold 0.90</code></pre>
  </li>
  
</ul>

<h2>2) MinHash (Jaccard LSH)</h2>
<p><strong>What it does</strong>: Approximates Jaccard by hashing shingles into a compact signature (length = <code>--minhash-perm</code>), then compares signatures to estimate similarity.</p>
<ul>
  <li><strong>Parameters</strong>: <code>--shingle-size k</code>, <code>--minhash-perm N</code> (default 128)</li>
  <li><strong>Complexity</strong>: O(k·|A| + k·|B|) to build signatures; O(N) compare</li>
  <li><strong>Strengths</strong>: Much faster comparisons at scale; memory‑friendly for large inputs.</li>
  <li><strong>Limitations</strong>: Probabilistic estimate; very small <code>N</code> reduces accuracy. Not ideal for extremely short texts.</li>
  <li><strong>Use when</strong>: You need scalable similarity over many candidates or large files.</li>
  <li><strong>Example</strong>:
    <pre><code>--similarity-mode minhash --shingle-size 5 --minhash-perm 128 --similarity-threshold 0.90</code></pre>
  </li>
  
</ul>

<h2>3) SimHash (64‑bit)</h2>
<p><strong>What it does</strong>: Projects tokens into a 64‑bit fingerprint where Hamming distance approximates content similarity. Score = <code>1 − HD/64</code>.</p>
<ul>
  <li><strong>Parameters</strong>: none beyond tokenization</li>
  <li><strong>Complexity</strong>: O(|tokens|) per document to compute; O(1) to compare</li>
  <li><strong>Strengths</strong>: Extremely compact and fast; great for near‑duplicate detection.</li>
  <li><strong>Limitations</strong>: Lower resolution than Jaccard/MinHash; may blur subtle differences.</li>
  <li><strong>Use when</strong>: You want quick near‑duplicate detection at large scale.</li>
  <li><strong>Example</strong>:
    <pre><code>--similarity-mode simhash --similarity-threshold 0.90</code></pre>
  </li>
  
</ul>

<h2>4) Char n‑gram Jaccard</h2>
<p><strong>What it does</strong>: Builds a normalized ASCII token stream, then takes contiguous character n‑grams and compares sets with Jaccard.</p>
<ul>
  <li><strong>Parameters</strong>: <code>--char-ngram-size n</code> (default 5)</li>
  <li><strong>Complexity</strong>: O(L) to extract n‑grams; set Jaccard as above</li>
  <li><strong>Strengths</strong>: Sensitive to small edits, whitespace, punctuation changes.</li>
  <li><strong>Limitations</strong>: For very long texts, the n‑gram set can be large; not robust to major re‑ordering.</li>
  <li><strong>Use when</strong>: You expect minor textual edits and want higher sensitivity.</li>
  <li><strong>Example</strong>:
    <pre><code>--similarity-mode charjaccard --char-ngram-size 5 --similarity-threshold 0.90</code></pre>
  </li>
  
</ul>

<h2>5) Winnow (token shingles)</h2>
<p><strong>What it does</strong>: Hashes token shingles, slides a window, and selects minimums (rightmost on ties) as fingerprints; compares sets via Jaccard.</p>
<ul>
  <li><strong>Parameters</strong>: <code>--shingle-size k</code>, <code>--winnow-window w</code> (default 4)</li>
  <li><strong>Complexity</strong>: O(|shingles|) to fingerprint; set Jaccard for compare</li>
  <li><strong>Strengths</strong>: Compact fingerprints; resilient to small shifts; good for long texts.</li>
  <li><strong>Limitations</strong>: Fingerprint selection can hide subtle differences; parameter tuning affects recall/precision.</li>
  <li><strong>Use when</strong>: You want compact, shift‑resistant matching on larger files.</li>
  <li><strong>Example</strong>:
    <pre><code>--similarity-mode winnow --shingle-size 5 --winnow-window 4 --similarity-threshold 0.85</code></pre>
  </li>
  
</ul>

<hr>

<h2>Choosing Parameters</h2>
<ul>
  <li><strong>Threshold</strong>: Higher = stricter matches (fewer candidates). Start at <code>0.9</code> for MinHash/SimHash, <code>0.92</code> for Jaccard/Char/Winnow, then adjust.</li>
  <li><strong>Shingle size (k)</strong>: Larger k increases precision but reduces recall; smaller k increases sensitivity.</li>
  <li><strong>MinHash permutations (N)</strong>: 64–256 is typical. Larger N improves stability at added cost.</li>
  <li><strong>Char n</strong>: 4–6 balances sensitivity and noise.</li>
  <li><strong>Winnow window (w)</strong>: 3–6 is common; larger windows pick fewer minima (more compact, potentially less sensitive).</li>
  
</ul>
