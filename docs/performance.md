<h1>⚡ Performance</h1>

<p>Find-Commit provides several options to balance speed vs. completeness.</p>

<h2>Clone/Fetch</h2>
<ul>
  <li><code>--shallow</code>: Shallow clones reduce fetch time and disk usage. Combine with <code>--depth</code>.</li>
  <li><code>--depth N</code>: Depth for shallow clone. Depth 1 is fastest but may miss older commits.</li>
  <li><code>--selective</code>: Fetch only the main branch and tags for a smaller graph.</li>
  <li><code>--parallel-fetch</code>: Enable parallel fetching (experimental).</li>
  
</ul>

<h2>Fast Mode</h2>
<ul>
  <li><code>--fast</code> is a shortcut enabling shallow + selective, disabling progress/timing, and skipping expensive per-candidate branch lookups when writing outputs.</li>
  <li>Best for quick iterations where exactness of branch metadata is less critical.</li>
  
</ul>

<h2>Progress &amp; Timings</h2>
<ul>
  <li><code>--progress</code> renders a simple spinner/progress bar to stderr during long steps.</li>
  <li><code>--timings</code> records per-step durations and wall timestamps. Slight overhead but helpful for profiling.</li>
  
</ul>

<h2>Path Hints</h2>
<ul>
  <li>Providing <code>--repo-file-path</code> can dramatically reduce fallback scanning time by avoiding a broad filename search.</li>
  
</ul>

<h2>Blob-First Optimization</h2>
<ul>
  <li>During fallback, a blob-id check is attempted before reading file contents. This avoids content I/O when object ids already match.</li>
  
</ul>
