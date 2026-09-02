import { copyFile, mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const publicDirectory = resolve(root, 'public');

await mkdir(publicDirectory, { recursive: true });
await Promise.all([
  copyFile(resolve(root, 'ui/index.html'), resolve(publicDirectory, 'growth-os.html')),
  copyFile(resolve(root, 'ui/styles.css'), resolve(publicDirectory, 'styles.css')),
  copyFile(resolve(root, 'ui/app.js'), resolve(publicDirectory, 'app.js')),
  copyFile(resolve(root, 'ui/effects.js'), resolve(publicDirectory, 'effects.js')),
]);
