<h1>🏗️ Architecture</h1>

<h2>Top‑Level Flow</h2>
<ol>
  <li>Parse CLI args in <code>find_commits.py</code> and delegate to <code>find_commits_lib.core.orchestrate.orchestrate(args)</code></li>
  <li>Prepare repository (<code>ensure_repo</code>), optionally fetch forks</li>
  <li>Compute local blob ids (LF-normalized, and CRLF on Windows)</li>
  <li>Attempt exact blob match across all refs</li>
  <li>If none found, build candidate repo paths and collect commits touching them</li>
  <li>Evaluate candidates using chosen similarity mode; apply threshold to include top matches</li>
  <li>Rank and pick preferred commit; write report/env outputs; cleanup cache</li>
  
</ol>

<h2>Key Modules</h2>
<ul>
  <li><code>find_commits_lib/core/orchestrate.py</code>: Orchestrates the full process, timing, progress, and outputs.</li>
  <li><code>find_commits_lib/git_ops.py</code>: Shells out to <code>git</code> for clone/fetch, rev-parse, log, show, etc.</li>
  <li><code>find_commits_lib/github_api.py</code>: Queries GitHub REST API to list forks and repo details; wires remotes.</li>
  <li><code>find_commits_lib/fuzzy.py</code>: Tokenization, Jaccard, MinHash, SimHash, Char n-grams, Winnowing.</li>
  <li><code>find_commits_lib/selection.py</code>: Chooses a preferred commit and representative branch.</li>
  <li><code>find_commits_lib/utils.py</code>: Repo dir utilities, cleanup, progress bars, timing formatters.</li>
  
</ul>

<h2>Data &amp; Outputs</h2>
<ul>
  <li>Report: human-readable with mode, preferred, local blob ids, fork stats, and candidate listing.</li>
  <li>Env: key-value pairs for automation; includes branch details unless in fast mode.</li>
  <li>Timings: step start/end/ms are collated at the end for both outputs (skipped in fast mode).</li>
  
</ul>

<h2>Performance Notes</h2>
<ul>
  <li>Refspecs are normalized to fetch all heads/tags; PR refs added for origin when available.</li>
  <li>Fallback evaluation prefers cheap blob-id checks before reading content.</li>
  <li>Fast mode disables slow per-candidate branch lookups.</li>
  
</ul>
