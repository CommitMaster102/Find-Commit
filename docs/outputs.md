<h1>🧾 Outputs</h1>

<p>On success, the tool prints a summary to stderr, and writes two files by default:</p>
<ul>
  <li><code>find_commits.txt</code>: Human-readable report.</li>
  <li><code>find_commits.env</code>: Env-style key/values you can source or parse.</li>
  
</ul>

<h2>Report File (<code>find_commits.txt</code>)</h2>
<ul>
  <li><code>mode=&lt;search_mode&gt;</code>: One of <code>exact_blob</code>, <code>normalized_path</code>, or the selected similarity.</li>
  <li><code>preferred=&lt;commit_sha&gt;</code>: Preferred commit among candidates.</li>
  <li><code>local_blob_norm=&lt;oid&gt;</code>: Normalized LF blob id for the local file.</li>
  <li><code>local_blob_raw=&lt;oid&gt;</code>: Windows-only alternate CRLF blob id when applicable.</li>
  <li><code>forks_fetched</code>, <code>forks_discovered</code>, <code>forks_selected</code> when forks were included.</li>
  <li><code>candidates_count=&lt;n&gt;</code> and a <code>candidates:</code> block.</li>
  <li>Fast mode: each candidate line is <code>- commit=&lt;sha&gt;</code></li>
  <li>Normal mode: each line is <code>- commit=&lt;sha&gt; ts=&lt;unix_ts&gt; branches=&lt;list&gt;</code></li>
  
</ul>

<h2>Env File (<code>find_commits.env</code>)</h2>
<ul>
  <li><code>PREFERRED_COMMIT=&lt;sha&gt;</code></li>
  <li><code>CANDIDATE_COMMITS= -&gt; \n"&lt;sha1&gt;\t\n&lt;sha2&gt;..."</code> (tab-escaped newlines between entries)</li>
  <li><code>MATCH_MODE=&lt;search_mode&gt;</code></li>
  <li>Fork stats when applicable: <code>FORKS_FETCHED</code>, <code>FORKS_DISCOVERED</code>, <code>FORKS_SELECTED</code>.</li>
  <li>When not in fast mode, also:
    <ul>
      <li><code>PREFERRED_BRANCH=&lt;branch&gt;</code></li>
      <li><code>PREFERRED_BRANCHES="&lt;b1&gt;\t\n&lt;b2&gt;..."</code></li>
      
    </ul>
  </li>
  
</ul>

<h2>Timings</h2>
<ul>
  <li>If <code>--timings</code> is set (and not <code>--fast</code>), the tool appends timing keys to both outputs:</li>
  <li>Text report: <code>&lt;step&gt;_start=...</code>, <code>&lt;step&gt;_end=...</code>, <code>&lt;step&gt;_difference_time=...</code> (humanized)</li>
  <li>Env file: <code>&lt;STEP&gt;_START=...</code>, <code>&lt;STEP&gt;_END=...</code>, <code>&lt;STEP&gt;_DIFFERENCE_TIME=...</code></li>
  <li>Typical steps: <code>read_local_file</code>, <code>prepare_repo</code>, <code>fetch_forks</code>, <code>compute_local_blobs</code>, <code>search_exact</code>, <code>build_candidate_paths</code>, <code>collect_touches</code>, <code>prepare_fingerprints</code>, <code>evaluate_candidates</code>, <code>apply_fuzzy_threshold</code>, <code>process_candidates</code>, <code>choose_preferred</code>, <code>write_report</code>, <code>write_env</code>, <code>cleanup</code>, <code>total</code>.</li>
  
</ul>
