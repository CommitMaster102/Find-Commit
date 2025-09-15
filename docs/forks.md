
<h1>🍴 Fork Discovery</h1>

<p>
  Enable <code>--include-forks</code> to discover GitHub forks for the target repository and fetch their refs into the local clone before searching. This expands the search space across forks.
</p>

<h2>Behavior</h2>
<ul>
  <li>Parses the target URL for GitHub owner/repo. Non-GitHub URLs skip fork discovery.</li>
  <li>If the target repo is itself a fork, it also queries the parent’s forks and prioritizes those after deduplication by <code>full_name</code>.</li>
  <li>Adds each selected fork as a unique remote (<code>fork_&lt;owner&gt;_&lt;repo&gt;</code> with suffixes for collisions), configures fetch refspecs for heads and tags, then fetches.</li>
  
</ul>

<h2>Rate Limits &amp; Auth</h2>
<ul>
  <li>Unauthenticated GitHub API calls are rate-limited. Set <code>GITHUB_TOKEN</code> or pass <code>--github-token TOKEN</code> to increase limits.</li>
  
</ul>

<h2>Selection Window</h2>
<ul>
  <li><code>--forks-limit N</code>: number of forks to fetch (1–99). Default: 20.</li>
  <li><code>--forks-offset N</code>: offset into the deduplicated list before selecting. Useful for paging newer/older forks.</li>
  
</ul>

<h2>Outputs</h2>
<ul>
  <li>When forks are included, outputs include <code>FORKS_FETCHED</code>, <code>FORKS_DISCOVERED</code>, and <code>FORKS_SELECTED</code> in both report and env files.</li>
  
</ul>

<h2>Caveats</h2>
<ul>
  <li>Fork discovery is best-effort. Network/API errors are tolerated; missing forks are simply skipped.</li>
  <li>Some remotes do not expose PR refs; PR-specific fetch refspecs are added only for <code>origin</code> and may be ignored for forks.</li>
  
</ul>
