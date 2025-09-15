<h1>🛠️ Troubleshooting &amp; FAQ</h1>

<h2>Common Issues</h2>
<ul>
  <li>
    Error: <code>--forks-limit cannot be greater than 99.</code><br>
    ➤ Reduce <code>--forks-limit</code> to 99 or less.
  </li>
  <li>
    No candidate paths were discovered<br>
    ➤ Provide <code>--repo-file-path</code> if you know the likely path in the repo.<br>
    ➤ Ensure the local filename matches repository filenames if relying on filename matching.
  </li>
  <li>
    No candidates found<br>
    ➤ Try a different similarity mode or lower <code>--similarity-threshold</code>.<br>
    ➤ Increase search completeness by disabling <code>--shallow</code> or <code>--selective</code>.<br>
    ➤ Include forks: <code>--include-forks</code> (consider setting <code>GITHUB_TOKEN</code>).
  </li>
  <li>
    Not a GitHub repository<br>
    ➤ Fork discovery is only supported for GitHub URLs. The core search works for any Git remote that Git can clone.
  </li>
  
</ul>

<h2>FAQ</h2>
<ul>
  <li>
    Q: Will shallow clone miss matches?<br>
    A: Yes, if the matching commit is older than the fetched depth/refs. Use larger <code>--depth</code> or disable shallow.
  </li>
  <li>
    Q: What does preferred commit mean?<br>
    A: The tool ranks candidates and then selects a single preferred commit. Branch priority is applied (origin/main/master/release/x.y) or the most recent commit otherwise.
  </li>
  <li>
    Q: What’s emitted in outputs when <code>--fast</code> is used?<br>
    A: Outputs omit branch metadata and timing keys; candidate lines in the report only include commit SHAs.
  </li>
  
</ul>
