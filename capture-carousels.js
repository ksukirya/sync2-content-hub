#!/usr/bin/env node

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');

const CAROUSEL_DIR = path.join(__dirname, 'carousels');
const HTML_FILE = path.join(__dirname, 'carousel-generator.html');

// Carousel definitions
const carousels = [
  { id: 1, slides: 7 },
  { id: 2, slides: 7 },
  { id: 3, slides: 7 },
  { id: 4, slides: 7 },
  { id: 5, slides: 6 }
];

async function captureCarousels() {
  console.log('🚀 Starting carousel capture...\n');
  
  // Ensure output directory exists
  if (!fs.existsSync(CAROUSEL_DIR)) {
    fs.mkdirSync(CAROUSEL_DIR, { recursive: true });
  }
  
  // Launch browser
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });
  
  const page = await browser.newPage();
  
  // Set viewport to slide dimensions
  await page.setViewport({
    width: 1080,
    height: 1350,
    deviceScaleFactor: 1
  });
  
  // Load the HTML file
  const fileUrl = `file://${HTML_FILE}`;
  await page.goto(fileUrl, { waitUntil: 'networkidle0' });
  
  // Wait for fonts to load
  await page.evaluate(() => document.fonts.ready);
  await new Promise(r => setTimeout(r, 1000)); // Extra wait for rendering
  
  // Capture each slide
  for (const carousel of carousels) {
    console.log(`📸 Capturing Carousel ${carousel.id}...`);
    
    for (let slide = 1; slide <= carousel.slides; slide++) {
      const slideId = `carousel-${carousel.id}-slide-${slide}`;
      const filename = `carousel-${carousel.id}-slide-${slide}.png`;
      const outputPath = path.join(CAROUSEL_DIR, filename);
      
      // Find and capture the slide element
      const element = await page.$(`#${slideId}`);
      
      if (element) {
        await element.screenshot({
          path: outputPath,
          type: 'png'
        });
        console.log(`  ✅ ${filename}`);
      } else {
        console.log(`  ❌ Could not find #${slideId}`);
      }
    }
    
    // Create tar.gz bundle for this carousel
    const bundleName = `carousel-${carousel.id}-all-slides.tar.gz`;
    const slideFiles = [];
    for (let s = 1; s <= carousel.slides; s++) {
      slideFiles.push(`carousel-${carousel.id}-slide-${s}.png`);
    }
    
    try {
      execSync(`tar -czf ${bundleName} ${slideFiles.join(' ')}`, {
        cwd: CAROUSEL_DIR
      });
      console.log(`  📦 ${bundleName}\n`);
    } catch (err) {
      console.log(`  ⚠️  Failed to create bundle: ${err.message}\n`);
    }
  }
  
  await browser.close();
  
  console.log('✨ All carousels captured successfully!\n');
  
  // Summary
  console.log('Generated files:');
  const files = fs.readdirSync(CAROUSEL_DIR).filter(f => f.endsWith('.png') || f.endsWith('.tar.gz'));
  files.forEach(f => console.log(`  - ${f}`));
}

captureCarousels().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
