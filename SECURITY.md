# Security Policy

## Supported Versions

MemoryBridge is a prototype built for the Google "Agents for Good" hackathon. It is not currently maintained as a production product with guaranteed long-term support.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.0   | :white_check_mark: |
| < 0.1.0 | :x:                |

## Prototype & Educational Disclaimer

**MemoryBridge is a prototype and proof-of-concept.**
- It is **not a medical device**.
- It does **not** diagnose, treat, cure, or prevent any disease, including dementia.
- It should **never** be used with real protected health information (PHI) or personal data without undergoing a full HIPAA/GDPR compliance review and professional medical validation.
- All data in the public demo is strictly synthetic.

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it privately.

**DO NOT submit sensitive information, credentials, or secrets in public GitHub issues or pull requests.**

To report a vulnerability, please email `security@memorybridge.app` (placeholder for hackathon). Provide a detailed description of the issue, the steps to reproduce it, and any potential mitigations you suggest. We will attempt to acknowledge your report within 48 hours.

## Secret Management

If you accidentally commit a secret (like an API key, Neon database URL, or session secret) to a fork of this repository:
1. Revoke the secret immediately in the issuing provider's console.
2. Do not attempt to mask it with a new commit. The secret is already compromised in the git history.
3. Generate a new secret.
