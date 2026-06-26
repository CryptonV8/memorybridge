import type { NextConfig } from "next";

// Security headers applied to all routes.
//
// CSP notes:
//   - font-src 'self'  : Geist/GeistMono loaded via next/font are self-hosted at
//                        /_next/static/media/ — no remote font exceptions required.
//   - script-src 'unsafe-inline' : Required by Next.js 16 App Router inline
//                                  hydration scripts. Nonce-based CSP deferred to Phase 6.
//   - style-src 'unsafe-inline'  : Required by CSS-in-JS and Next.js runtime styles.
//   - img-src 'self' data: blob: : Allows inline SVGs and blob URLs used in UI.
//   - frame-ancestors 'none'     : Prevents clickjacking via iframe embedding.
//
// Exceptions are documented inline. No exceptions for remote CDNs or Google Fonts.
const securityHeaders = [
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob:",
      "font-src 'self'",
      "connect-src 'self'",
      "frame-ancestors 'none'",
      "object-src 'none'",
      "base-uri 'self'",
      "form-action 'self'",
    ].join("; "),
  },
  {
    key: "X-Content-Type-Options",
    value: "nosniff",
  },
  {
    key: "Referrer-Policy",
    value: "strict-origin-when-cross-origin",
  },
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=(), payment=()",
  },
  {
    key: "X-Frame-Options",
    value: "DENY",
  },
];

const nextConfig: NextConfig = {
  // Enable standalone output for Docker — copies only the files needed to run
  // the server, avoiding bundling node_modules that are already in the image.
  output: "standalone",

  async redirects() {
    return [
      {
        source: "/maria",
        destination: "/today",
        permanent: false,
      },
    ];
  },

  async headers() {
    return [
      {
        // Apply security headers to all routes
        source: "/(.*)",
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;

