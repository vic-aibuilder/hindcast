# GitHub Setup Notes

## Branch protection (main)

Settings → Branches → Add branch protection rule for `main`:

- [x] Require a pull request before merging
- [x] Require status checks to pass — add the `test` job from CI
- [x] Require branches to be up to date before merging
- [x] Do not allow bypassing the above settings

## Secrets

The CI workflow doesn't require secrets for lint + test. When integration tests are
added, wire keys in Settings → Secrets and variables → Actions:

| Secret name | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com |
| `TAVILY_API_KEY` | Tavily dashboard — verify plan/tier at build time |

## CODEOWNERS

`.github/CODEOWNERS` is configured for all three owners:
`@vic-aibuilder`, `@Christianalmonte112`, `@G3RRYGL3Z`.
