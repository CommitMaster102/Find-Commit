<h1>🧰 Installation</h1>

<h2>Requirements</h2>
<ul>
  <li>Python <code>&ge; 3.10</code></li>
  <li>Git available on your <code>PATH</code></li>
  <li>Optional: <code>GITHUB_TOKEN</code> environment variable to raise GitHub API rate limits when using fork discovery</li>
  
</ul>

<h2>Steps</h2>
<ol>
  <li>
    Clone the repository:
    <pre><code>git clone https://github.com/CommitMaster102/Find-Commit.git
cd Find-Commit</code></pre>
  </li>
  <li>
    (Optional) Create a virtual environment:
    <ul>
      <li>Windows PowerShell:<br><code>python -m venv .venv; .venv\Scripts\Activate.ps1</code></li>
      <li>Unix/macOS:<br><code>python -m venv .venv &amp;&amp; source .venv/bin/activate</code></li>
      
    </ul>
  </li>
  <li>
    Run the CLI directly:
    <pre><code>python find_commits.py &lt;local_file&gt; &lt;repo_url&gt; [options]</code></pre>
  </li>
  
</ol>

<h2>Tip</h2>
<p>For GitHub API calls, set <code>GITHUB_TOKEN</code> to reduce rate-limiting when <code>--include-forks</code> is enabled.</p>
