# Security Policy

This project handles credential material. Treat input files, terminal scrollback,
and generated result files as sensitive.

## Safe Handling

- Use the tool only on WordPress sites you own or are explicitly authorized to
  test.
- Keep TLS verification enabled. Use `--insecure` only for isolated lab systems.
- Do not commit Hydra output, credential files, result files, logs, `.env`
  files, private keys, or screenshots that expose credentials.
- Rotate any real credential that was committed to public history.

## Reporting Issues

Report vulnerabilities through a private GitHub security advisory or another
private channel. Do not open public issues containing target URLs, usernames,
passwords, tokens, logs, or result files.

## Historical Exposure

Earlier public history included generated `VertaBassh_results_*.txt` files. If
any value in those files was real, rotate it and purge or recreate public
history so the old blobs are no longer reachable.
