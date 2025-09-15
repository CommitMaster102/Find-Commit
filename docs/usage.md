<h1>📖 Usage</h1>

<h2>Basic</h2>
<p>
  <code>python find_commits.py &lt;local_file&gt; &lt;repo_url&gt; [--timings]</code><br>
  <em>&lt;local_file&gt;</em> can be a path or <code>-</code> to read from stdin.<br>
  <em>&lt;repo_url&gt;</em> is a Git remote such as <code>https://github.com/org/repo.git</code>.
</p>

<h2>Examples</h2>
<ul>
  <li>
    Exact search with timings
    <pre><code>python find_commits.py path/to/file.txt https://github.com/org/repo.git --timings</code></pre>
  </li>
  <li>
    Read file from stdin
    <pre><code># Windows (PowerShell)
type path\to\file.txt | python find_commits.py - https://github.com/org/repo.git --timings

# Unix
cat path/to/file.txt | python find_commits.py - https://github.com/org/repo.git --timings</code></pre>
  </li>
  <li>
    Provide a path hint for fallback (no exact blob)
    <pre><code>python find_commits.py file.txt https://github.com/org/repo.git --repo-file-path src/file.txt --timings</code></pre>
  </li>
  <li>
    Include forks with token and selection window
    <pre><code>python find_commits.py file.txt https://github.com/org/repo.git \
  --include-forks --github-token "$GITHUB_TOKEN" --forks-limit 30 --forks-offset 10 --timings</code></pre>
  </li>
  <li>
    Use MinHash for approximate matching
    <pre><code>python find_commits.py file.txt https://github.com/org/repo.git \
  --similarity-mode minhash --similarity-threshold 0.9 --shingle-size 5 --minhash-perm 128 --timings --progress</code></pre>
  </li>
  <li>
    Use SimHash
    <pre><code>python find_commits.py file.txt https://github.com/org/repo.git \
  --similarity-mode simhash --similarity-threshold 0.9 --timings --progress</code></pre>
  </li>
  <li>
    Customize outputs and repo cache
    <pre><code>python find_commits.py file.txt https://github.com/org/repo.git \
  --repo-dir .repo_tmp --out-report report.txt --out-env env.out --timings</code></pre>
  </li>
  <li>
    Shallow clone for speed
    <pre><code>python find_commits.py file.txt https://github.com/org/repo.git --shallow --depth 10 --timings</code></pre>
  </li>
  <li>
    Fast mode (quick run)
    <pre><code>python find_commits.py file.txt https://github.com/org/repo.git --fast --timings</code></pre>
  </li>
  <li>
    Selective fetch with parallel fetch
    <pre><code>python find_commits.py file.txt https://github.com/org/repo.git --selective --parallel-fetch --timings</code></pre>
  </li>
  
</ul>

<h2>Notes</h2>
<ul>
  <li>The tool first searches for exact blob matches. If none are found, it scans commits touching candidate paths and applies the selected similarity algorithm.</li>
  <li>During fallback, a fast blob-id check is attempted before reading file contents to avoid unnecessary I/O.</li>
  
</ul>
