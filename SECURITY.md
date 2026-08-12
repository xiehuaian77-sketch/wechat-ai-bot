# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please send an email to the maintainers or open a private security advisory through GitHub Security tab.

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Within 48 hours**: Acknowledge receipt of your report
- **Within 7 days**: Provide initial assessment and remediation plan
- **Within 30 days**: Release a patch or mitigation

## Security Best Practices

### For Users

1. **Never expose your `.env` file** — It contains sensitive API keys and secrets
2. **Use strong `JWT_SECRET_KEY`** — Generate a cryptographically secure random key
3. **Enable HTTPS in production** — Never run without TLS in production
4. **Restrict CORS origins** — Only allow trusted domains
5. **Keep dependencies updated** — Regularly run `pip audit` and update packages

### For Contributors

1. **Never commit secrets** — Use `.env.example` as template, never include real credentials
2. **Validate all inputs** — Use Pydantic models for request validation
3. **Use parameterized queries** — Prevent SQL injection via SQLAlchemy ORM
4. **Log security events** — Authentication failures, permission denials, etc.
5. **Rate limiting** — The app includes rate limiting middleware, respect it

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | ✅ Yes             |
| < 0.1   | ❌ No              |

## Security Audit

This project undergoes periodic security audits. See [SECURITY_AUDIT.md](SECURITY_AUDIT.md) for the latest audit results.

## Dependencies Security

We use `pip-audit` in CI to scan for known vulnerabilities in dependencies. Results are available in each CI run.
