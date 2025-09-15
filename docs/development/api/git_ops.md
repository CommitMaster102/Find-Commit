<h1>API: <code>git_ops</code></h1>

<p>Module: <code>find_commits_lib.git_ops</code></p>

<h2>Primary Functions</h2>
<ul>
  <li>
    <code>run(cmd, cwd=None, input_bytes=None, show_progress=False) -&gt; str</code><br>
    Validates <code>git</code> prefix; runs command; raises <code>RuntimeError</code> on non-zero.
  </li>
  <li>
    <code>ensure_repo(repo_dir, repo_url, shallow=False, depth=1, selective=False, parallel=False, show_progress=False, fast_mode=False) -&gt; None</code><br>
    Clones or updates a repo; normalizes refspecs; attempts unshallow when applicable.
  </li>
  <li>
    <code>discover_paths_by_filename(repo_dir, filename) -&gt; list[str]</code><br>
    Scans <code>git rev-list --objects --all</code> for paths ending with <code>filename</code>.
  </li>
  <li>
    <code>file_content_at(repo_dir, commit, repo_file_path) -&gt; bytes | None</code><br>
    Returns file bytes for <code>commit:path</code> or <code>None</code>.
  </li>
  <li>
    <code>blob_id_at(repo_dir, commit, repo_file_path) -&gt; str | None</code><br>
    Returns the blob object id for <code>commit:path</code> (40 hex) or <code>None</code>.
  </li>
  <li>
    <code>find_exact_blob_commits(repo_dir, blob_oid_norm, blob_oid_raw) -&gt; list[str]</code><br>
    Returns commits with a matching blob object id across all refs.
  </li>
  <li>
    <code>commits_touching_path(repo_dir, repo_file_path) -&gt; list[str]</code><br>
    Returns commit hashes that touched a given path (<code>--all --follow</code>).
  </li>
  <li>
    <code>branches_containing(repo_dir, commit) -&gt; list[str]</code><br>
    Returns remote branches containing a commit.
  </li>
  <li>
    <code>commit_timestamp(repo_dir, commit) -&gt; int</code><br>
    Unix timestamp of a commit, or <code>0</code> if not parseable.
  </li>
  <li>
    <code>existing_remote_names(repo_dir) -&gt; list[str]</code>, <code>sanitize_remote_name(candidate) -&gt; str</code>, <code>ensure_remote_with_refspec(repo_dir, name, url) -&gt; None</code><br>
    Helpers for remote wiring and safe naming.
  </li>
  
</ul>
