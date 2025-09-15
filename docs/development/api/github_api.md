<h1>API: <code>github_api</code></h1>

<p>Module: <code>find_commits_lib.github_api</code></p>

<h2>Primary Functions</h2>
<ul>
  <li>
    <code>parse_github_owner_repo(repo_url) -&gt; (owner, repo) | None</code><br>
    Extracts owner/repo from common HTTPS/SSH GitHub URL forms.
  </li>
  <li>
    <code>github_api_get(url, token) -&gt; (status, bytes)</code><br>
    HTTPS-only request helper; returns status/body; tolerates HTTP/URL errors.
  </li>
  <li>
    <code>github_repo_details(owner, repo, token) -&gt; (status, dict | None)</code><br>
    Basic repo metadata; prints helpful diagnostics on errors.
  </li>
  <li>
    <code>list_github_forks(owner, repo, token, max_forks) -&gt; list[dict]</code><br>
    Paginates forks up to <code>max_forks</code>.
  </li>
  <li>
    <code>fetch_forks_into_repo(repo_dir, repo_url, token, max_forks, forks_offset) -&gt; (added, discovered, selected)</code><br>
    Adds unique remotes for a selection window of forks, fetches their refs.
  </li>
  
</ul>
