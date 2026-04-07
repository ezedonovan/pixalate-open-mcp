# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in the Pixalate Open MCP server, please report it responsibly.

**Email:** security@pixalate.com

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact

We will acknowledge receipt within 3 business days and provide an initial assessment within 10 business days.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |

## Security Practices

- API keys are loaded from environment variables only — never hardcoded or logged
- User-supplied parameters (IPs, device IDs, domains) are not written to log files
- All API communication uses HTTPS
- No conversation data is collected or stored
