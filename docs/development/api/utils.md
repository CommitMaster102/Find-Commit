<h1>API: <code>utils</code></h1>

<p>Module: <code>find_commits_lib.utils</code></p>

<h2>Filesystem &amp; Repo Cache</h2>
<ul>
  <li><code>normalize_lf(content) -&gt; bytes</code></li>
  <li><code>repo_basename_from_url(repo_url) -&gt; str</code></li>
  <li><code>default_repo_dir_for(repo_url) -&gt; Path</code></li>
  <li><code>force_remove_dir(path) -&gt; None</code></li>
  <li><code>cleanup_repo_cache(repo_dir, repo_url) -&gt; None</code></li>
  
</ul>

<h2>Progress &amp; Timing</h2>
<ul>
  <li><code>Spinner(enabled)</code> with <code>.tick(label)</code> and <code>.clear()</code></li>
  <li><code>AutoProgressBar(enabled)</code> used via <code>StepDisplay</code></li>
  <li><code>StepDisplay(step_key, pretty_label, timings, progress, print_to_stderr)</code><br>Context manager recording <code>&lt;step&gt;_start</code>, <code>&lt;step&gt;_end</code>, and <code>&lt;step&gt;_ms</code> into <code>timings</code>.</li>
  <li><code>StepTimer(name, on_done, spinner=None)</code></li>
  
</ul>

<h2>Formatting</h2>
<ul>
  <li><code>format_ms(dt_seconds) -&gt; str</code></li>
  <li><code>format_timestamp_ms(ts=None) -&gt; str</code></li>
  <li><code>format_duration_human(ms) -&gt; str</code></li>
  
</ul>
