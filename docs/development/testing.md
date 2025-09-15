<h1>🧪 Testing</h1>

<h2>Local</h2>
<ul>
  <li>Create a virtualenv and install dev deps if needed.</li>
  <li>Run tests: <code>pytest -q</code></li>
  <li>Coverage (optional): <code>pytest --cov --cov-report=term-missing</code></li>
  
</ul>

<h2>What Tests Cover</h2>
<ul>
  <li>CLI orchestration wiring for all similarity modes and edge cases.</li>
  <li>GitHub API utilities (parsing, pagination, errors) with mocks.</li>
  <li>Git operations wrapper safety and behavior (progress flags, config, IDs).</li>
  <li>Fuzzy algorithms: tokenization, shingles, Jaccard, MinHash, SimHash, Char n-grams, Winnow.</li>
  <li>Progress/timing helpers and formatting.</li>
  <li>Selection rules for preferred commit/branch.</li>
  
</ul>

<h2>Notes</h2>
<ul>
  <li>Network and <code>git</code> commands are mocked in tests; they do not require real clones or API access.</li>
  <li>Use <code>-k</code> or test file filters for focused runs, e.g. <code>pytest -k similarity</code>.</li>
  
</ul>
