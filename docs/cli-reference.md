<h1>🧾 CLI Reference</h1>

<h2>Command</h2>
<p><code>python find_commits.py &lt;local_file&gt; &lt;repo_url&gt; [options]</code></p>

<h2>Required Positional Arguments</h2>
<ul>
  <li><code>local_file</code>: Path to the local file to match, or <code>-</code> to read from stdin.</li>
  <li><code>repo_url</code>: Target Git repository URL (e.g., <code>https://github.com/org/repo.git</code>).</li>
  
</ul>

<h2>Common Options</h2>
<ul>
  <li><code>--repo-dir PATH</code>: Local clone/cache directory. Default: <code>.repo_&lt;name&gt;</code> in CWD.</li>
  <li><code>--repo-file-path PATH</code>: Path inside the repo to scan if no exact blob is found.</li>
  <li><code>--out-env PATH</code>: Env-style output file path. Default: <code>find_commits.env</code>.</li>
  <li><code>--out-report PATH</code>: Human-readable report path. Default: <code>find_commits.txt</code>.</li>
  
</ul>

<h2>Fork Discovery</h2>
<ul>
  <li><code>--include-forks</code>: Discover and fetch GitHub forks before searching.</li>
  <li><code>--github-token TOKEN</code>: GitHub token (defaults to <code>$GITHUB_TOKEN</code> if set).</li>
  <li><code>--forks-limit INT</code>: Limit forks fetched (1–99). Default: <code>20</code>.</li>
  <li><code>--forks-offset INT</code>: Offset into the de-duplicated fork list. Default: <code>0</code>.</li>
  
</ul>

<h2>Similarity Fallback</h2>
<ul>
  <li><code>--similarity-mode {jaccard,minhash,simhash,charjaccard,winnow}</code>. Default: <code>jaccard</code>.</li>
  <li><code>--similarity-threshold FLOAT</code>: [0,1] threshold for candidate inclusion. Default: <code>0.92</code>.</li>
  <li><code>--shingle-size INT</code>: Token shingle size (Jaccard/MinHash/Winnow). Default: <code>5</code>.</li>
  <li><code>--char-ngram-size INT</code>: Character n-gram size for <code>charjaccard</code>. Default: <code>5</code>.</li>
  <li><code>--winnow-window INT</code>: Window size for <code>winnow</code>. Default: <code>4</code>.</li>
  <li><code>--minhash-perm INT</code>: Number of permutations for MinHash. Default: <code>128</code>.</li>
  
</ul>

<h2>Progress &amp; Timings</h2>
<ul>
  <li><code>--progress</code>: Show spinner/progress animation.</li>
  <li><code>--timings</code>: Print per-step timings to stderr and embed in outputs.</li>
  
</ul>

<h2>Clone/Fetch Performance</h2>
<ul>
  <li><code>--shallow</code>: Use shallow clone (may miss some commits if depth is small).</li>
  <li><code>--depth INT</code>: Depth for shallow clone. Default: <code>1</code>.</li>
  <li><code>--selective</code>: Fetch main branch + tags only for speed.</li>
  <li><code>--parallel-fetch</code>: Enable parallel fetching (experimental).</li>
  <li><code>--fast</code>: Shortcut: implies shallow + selective, disables progress/timing, and skips expensive branch lookups when writing outputs.</li>
  
</ul>

<h2>Exit Codes</h2>
<ul>
  <li><code>0</code>: Success; candidates found and outputs written.</li>
  <li><code>1</code>: No candidates found or recoverable workflow termination.</li>
  <li><code>2</code>: Invalid input/usage (e.g., <code>--forks-limit</code> &gt; 99), or missing local file.</li>
  
</ul>
