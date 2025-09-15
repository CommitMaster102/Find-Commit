<h1>API: <code>selection</code></h1>

<p>Module: <code>find_commits_lib.selection</code></p>

<h2>Primary Functions</h2>
<ul>
  <li>
    <code>choose_preferred(repo_dir, candidates) -&gt; str</code><br>
    Prefer commits on <code>origin/(trunk|main|master|release|&lt;x.y&gt;)</code>; otherwise most recent by timestamp.
  </li>
  <li>
    <code>choose_branch_for_commit(repo_dir, commit) -&gt; str</code><br>
    Prefer <code>origin/(trunk|main|master|release|&lt;x.y&gt;)</code>, then PR-like refs, else first remote branch.
  </li>
  
</ul>
