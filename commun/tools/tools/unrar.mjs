import { createExtractorFromFile } from 'node-unrar-js';
const [,, file, out] = process.argv;
const ex = await createExtractorFromFile({ filepath: file, targetPath: out });
let n=0; for (const f of ex.extract().files) n++;
console.log('extracted', n);
