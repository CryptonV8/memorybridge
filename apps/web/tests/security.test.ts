import fs from 'fs';
import path from 'path';

describe('Security: Token Exposure Scan', () => {
  it('ensures DEMO_CAREGIVER_TOKEN does not leak into the production client-side bundles', () => {
    const token = process.env.DEMO_CAREGIVER_TOKEN || 'test-sentinel-cg-token';
    const staticDir = path.resolve(__dirname, '../.next/static');

    if (!fs.existsSync(staticDir)) {
      console.warn('Production build .next/static directory not found, skipping scan.');
      return;
    }

    const scanDirectory = (dir: string) => {
      const files = fs.readdirSync(dir);
      for (const file of files) {
        const fullPath = path.join(dir, file);
        const stat = fs.statSync(fullPath);
        if (stat.isDirectory()) {
          scanDirectory(fullPath);
        } else if (stat.isFile() && (file.endsWith('.js') || file.endsWith('.map') || file.endsWith('.html') || file.endsWith('.txt'))) {
          const content = fs.readFileSync(fullPath, 'utf8');
          if (content.includes(token)) {
            throw new Error(`Security Violation: Caregiver token "${token}" found in client asset: ${fullPath}`);
          }
        }
      }
    };

    scanDirectory(staticDir);
  });
});
