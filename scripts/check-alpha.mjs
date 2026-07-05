import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { inflateSync } from "node:zlib";

const root = join(process.cwd(), "apps", "desktop", "src", "assets", "pet");
const pngSignature = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

function listPngFiles(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    const stat = statSync(path);
    if (stat.isDirectory()) return listPngFiles(path);
    return name.toLowerCase().endsWith(".png") ? [path] : [];
  });
}

function paeth(left, up, upLeft) {
  const estimate = left + up - upLeft;
  const leftDistance = Math.abs(estimate - left);
  const upDistance = Math.abs(estimate - up);
  const upLeftDistance = Math.abs(estimate - upLeft);
  if (leftDistance <= upDistance && leftDistance <= upLeftDistance) return left;
  if (upDistance <= upLeftDistance) return up;
  return upLeft;
}

function parsePng(buffer) {
  if (!buffer.subarray(0, 8).equals(pngSignature)) {
    throw new Error("not a PNG file");
  }

  let offset = 8;
  let width = 0;
  let height = 0;
  let bitDepth = 0;
  let colorType = 0;
  const idatChunks = [];
  let trns = null;

  while (offset < buffer.length) {
    const length = buffer.readUInt32BE(offset);
    const type = buffer.toString("ascii", offset + 4, offset + 8);
    const dataStart = offset + 8;
    const data = buffer.subarray(dataStart, dataStart + length);

    if (type === "IHDR") {
      width = data.readUInt32BE(0);
      height = data.readUInt32BE(4);
      bitDepth = data[8];
      colorType = data[9];
    } else if (type === "IDAT") {
      idatChunks.push(data);
    } else if (type === "tRNS") {
      trns = data;
    } else if (type === "IEND") {
      break;
    }

    offset = dataStart + length + 4;
  }

  return { width, height, bitDepth, colorType, trns, compressed: Buffer.concat(idatChunks) };
}

function bytesPerPixel(colorType, bitDepth) {
  if (bitDepth !== 8) return 0;
  if (colorType === 6) return 4;
  if (colorType === 4) return 2;
  if (colorType === 2) return 3;
  if (colorType === 0 || colorType === 3) return 1;
  return 0;
}

function unfilterScanlines(raw, width, height, bpp) {
  const rowBytes = width * bpp;
  const output = Buffer.alloc(rowBytes * height);
  let rawOffset = 0;

  for (let y = 0; y < height; y += 1) {
    const filter = raw[rawOffset];
    rawOffset += 1;
    const rowOffset = y * rowBytes;
    const previousRowOffset = rowOffset - rowBytes;

    for (let x = 0; x < rowBytes; x += 1) {
      const value = raw[rawOffset + x];
      const left = x >= bpp ? output[rowOffset + x - bpp] : 0;
      const up = y > 0 ? output[previousRowOffset + x] : 0;
      const upLeft = y > 0 && x >= bpp ? output[previousRowOffset + x - bpp] : 0;

      if (filter === 0) output[rowOffset + x] = value;
      else if (filter === 1) output[rowOffset + x] = (value + left) & 0xff;
      else if (filter === 2) output[rowOffset + x] = (value + up) & 0xff;
      else if (filter === 3) output[rowOffset + x] = (value + Math.floor((left + up) / 2)) & 0xff;
      else if (filter === 4) output[rowOffset + x] = (value + paeth(left, up, upLeft)) & 0xff;
      else throw new Error(`unsupported PNG filter ${filter}`);
    }
    rawOffset += rowBytes;
  }

  return output;
}

function hasTransparentPixels(path) {
  const png = parsePng(readFileSync(path));
  if (png.colorType === 3) {
    return Boolean(png.trns?.some((alpha) => alpha < 255));
  }
  if (png.colorType === 2) {
    return Boolean(png.trns);
  }
  if (png.colorType !== 4 && png.colorType !== 6) {
    return false;
  }

  const bpp = bytesPerPixel(png.colorType, png.bitDepth);
  if (!bpp) {
    throw new Error(`unsupported PNG color type ${png.colorType} with bit depth ${png.bitDepth}`);
  }

  const pixels = unfilterScanlines(inflateSync(png.compressed), png.width, png.height, bpp);
  const alphaOffset = png.colorType === 6 ? 3 : 1;
  for (let i = alphaOffset; i < pixels.length; i += bpp) {
    if (pixels[i] < 255) return true;
  }
  return false;
}

const files = listPngFiles(root);
let warnings = 0;

for (const file of files) {
  try {
    if (!hasTransparentPixels(file)) {
      warnings += 1;
      console.warn(`Warning: ${relative(process.cwd(), file)} may use fake transparency; alpha is fully opaque.`);
    }
  } catch (error) {
    warnings += 1;
    console.warn(`Warning: could not inspect ${relative(process.cwd(), file)}: ${error.message}`);
  }
}

console.log(`Checked ${files.length} PNG files. ${warnings} warning(s).`);
