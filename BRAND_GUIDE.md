# MurmurTone Brand Guide

**Version 1.0** | Last Updated: January 2026

---

## Table of Contents

1. [Brand Introduction](#brand-introduction)
2. [Logo System](#logo-system)
3. [Color Palette](#color-palette)
4. [Typography](#typography)
5. [Iconography](#iconography)
6. [Brand Voice & Messaging](#brand-voice--messaging)
7. [Visual Design System](#visual-design-system)
8. [Website Guidelines](#website-guidelines)
9. [Email Guidelines](#email-guidelines)
10. [Social Media Guidelines](#social-media-guidelines)
11. [Visual Expression](#visual-expression)
12. [Usage Examples](#usage-examples)

---

## Brand Introduction

### Brand Name
**MurmurTone** - Private, Local Voice-to-Text for Windows

Always capitalize as "MurmurTone" (never "Murmurtone", "murmurtone", or "Murmur Tone")

### Tagline
**"Your voice, locally."**

Short, memorable, emphasizes the core value proposition: offline/local processing.

### Brand Promise
MurmurTone empowers professionals to capture their thoughts instantly without sacrificing privacy. Fast, private voice-to-text that works offline.

### Core Values

#### 1. Privacy First
- 100% offline processing
- No cloud uploads, no data tracking
- Your voice never leaves your machine

#### 2. Simplicity
- One hotkey, instant transcription
- No configuration required out-of-the-box
- Lightweight, runs quietly in the background

#### 3. Reliability
- Local processing = no internet dependency
- Consistent performance every time
- Works anywhere, anytime

### Target Audience

**Primary:**
- Knowledge workers (writers, programmers, researchers)
- Professionals who value privacy
- Remote workers and freelancers
- Privacy advocates

**Secondary:**
- People with accessibility needs
- Non-native English speakers
- Power users who want control

---

## Logo System

### Logo Concept

**Primary:** Waveform + Lock (Privacy First)
- Visual: Sound waveform contained within or integrated with shield/lock shape
- Symbolism: Voice (waveform) + Privacy (lock) + Local (contained)
- Style: Modern, clean, minimalist, tech-forward

For detailed logo design specifications, see [LOGO_DESIGN_BRIEF.md](LOGO_DESIGN_BRIEF.md).

### Logo Variants

#### 1. Full Logo (Horizontal)
- Icon + "MurmurTone" wordmark
- Use: Website header, marketing materials, presentations
- Minimum width: 120px digital, 1" print

#### 2. Icon Only
- Square format, icon without text
- Use: App icon, favicons, system tray, social media profile
- Sizes: 16×16, 32×32, 64×64, 128×128, 256×256, 512×512, 1024×1024

#### 3. Wordmark Only
- "MurmurTone" text only
- Use: Footer, headers where icon is redundant
- Minimum height: 20px digital

#### 4. Reversed/White
- White/light version for dark backgrounds
- Use: Dark mode UI, dark marketing materials

#### 5. Monochrome
- Single color: #667eea or black
- Use: Print, limited color contexts, fax (if anyone still uses that)

### Clear Space

Minimum clear space around logo = height of "M" in "MurmurTone"

Apply on all four sides. This prevents crowding and maintains visual breathing room.

### Minimum Sizes

- **Digital:** 32px height (full logo), 16px (icon only)
- **Print:** 0.5" height (full logo), 0.25" (icon only)

### Logo Usage Do's and Don'ts

✅ **DO:**
- Use provided logo files
- Maintain proportions (don't stretch)
- Use on appropriate backgrounds (light logo on dark, dark logo on light)
- Ensure adequate clear space
- Use high-resolution files for print

❌ **DON'T:**
- Recreate or modify the logo
- Change colors outside approved palette
- Add effects (shadows, glows, bevels)
- Rotate the logo
- Place on busy backgrounds where logo isn't legible
- Stretch or distort
- Separate icon from wordmark in full logo variant

---

## Color Palette

### Primary Colors

#### Brand Gradient
The signature MurmurTone gradient - use for hero sections, primary CTAs, and major brand moments.

```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

#### Indigo Primary
Main brand color for secondary elements.

- **Hex:** `#667eea`
- **RGB:** 102, 126, 234
- **Use:** Secondary buttons, links, icons, accents

#### Purple Primary
Gradient end color, use sparingly as solid.

- **Hex:** `#764ba2`
- **RGB:** 118, 75, 162
- **Use:** Gradient end, dark accents

### Secondary Colors

#### Indigo Light
Lighter shade for hover states and backgrounds.

- **Hex:** `#8b9cf6`
- **RGB:** 139, 156, 246
- **Use:** Hover states, secondary CTAs, lighter accents

#### Indigo Dark
Darker shade for emphasis and contrast.

- **Hex:** `#4f5fcf`
- **RGB:** 79, 95, 207
- **Use:** Text on light backgrounds, emphasis, depth

#### Purple Light
Lighter purple for subtle accents.

- **Hex:** `#9566c0`
- **RGB:** 149, 102, 192
- **Use:** Accents, highlights, alternate hover states

#### Purple Dark
Darker purple for depth and grounding.

- **Hex:** `#5a3875`
- **RGB:** 90, 56, 117
- **Use:** Footer, dark UI elements, depth

### Neutrals

#### Charcoal
Primary text color for headings.

- **Hex:** `#222222`
- **RGB:** 34, 34, 34
- **Use:** H1, H2, primary headings

#### Slate
Secondary text color.

- **Hex:** `#333333`
- **RGB:** 51, 51, 51
- **Use:** H3-H5, subheadings, secondary text

#### Gray Medium
Tertiary text color.

- **Hex:** `#666666`
- **RGB:** 102, 102, 102
- **Use:** Body text, captions, less important text

#### Gray Light
Light gray for disabled states.

- **Hex:** `#999999`
- **RGB:** 153, 153, 153
- **Use:** Disabled text, placeholder text

#### Gray Subtle
Very light gray for borders.

- **Hex:** `#cccccc`
- **RGB:** 204, 204, 204
- **Use:** Borders, dividers, subtle separators

#### Silver
Background gray for cards.

- **Hex:** `#f5f5f5`
- **RGB:** 245, 245, 245
- **Use:** Card backgrounds, alternating rows, light sections

#### Off-White
Subtle off-white for page backgrounds.

- **Hex:** `#f9f9f9`
- **RGB:** 249, 249, 249
- **Use:** Page backgrounds (warmer than pure white)

#### Pure White
White for contrast.

- **Hex:** `#ffffff`
- **RGB:** 255, 255, 255
- **Use:** White backgrounds, text on dark

### Semantic Colors

#### Success
Green for success states.

- **Hex:** `#22c55e`
- **RGB:** 34, 197, 94
- **Use:** Transcription complete, validation success, positive feedback

#### Warning
Orange for warnings.

- **Hex:** `#f59e0b`
- **RGB:** 245, 158, 11
- **Use:** Trial expiring, attention needed, caution states

#### Error
Red for errors.

- **Hex:** `#ef4444`
- **RGB:** 239, 68, 68
- **Use:** Transcription failed, validation errors, critical issues

#### Info
Blue for informational states (reuse primary).

- **Hex:** `#667eea`
- **RGB:** 102, 126, 234
- **Use:** Information messages, tips, neutral notifications

### Accent Colors

Use sparingly (max 10% of any page) for feature differentiation.

#### Teal Accent
Highlight for AI features.

- **Hex:** `#14b8a6`
- **RGB:** 20, 184, 166
- **Use:** AI cleanup feature highlights, AI-related icons

#### Gold Accent
Premium features and Pro badges.

- **Hex:** `#fbbf24`
- **RGB:** 251, 191, 36
- **Use:** Pro badges, premium indicators, special callouts

### Color Usage Rules

1. **Gradient:** Use for hero sections, primary CTAs, major headings only. Don't overuse.
2. **Indigo Primary:** Secondary buttons, links, icons throughout the site.
3. **Neutrals:** All body text, backgrounds, structural UI elements.
4. **Semantic:** Only for status feedback - success, error, warning states.
5. **Accents:** Maximum 10% of any page. Use for feature differentiation only.

### Accessibility

All text color combinations meet WCAG AA standards:
- Charcoal (#222) on white = 16.9:1 ratio ✅
- Gray Medium (#666) on white = 5.7:1 ratio ✅
- Indigo Primary (#667eea) on white = 4.5:1 ratio ✅

---

## Typography

### Font Families

**Primary Font: Roboto Serif**

The desktop application uses bundled Roboto Serif font files for a softer, friendlier appearance.

```
Desktop App: Roboto Serif (bundled in assets/fonts/)
```

**Web/Marketing Fallback Stack:**
```css
font-family: 'Roboto Serif', Georgia, 'Times New Roman', serif;
```

**Why Roboto Serif?**
- Warm, approachable serif design
- Softer, friendlier feel than sans-serif alternatives
- Excellent readability at all sizes
- Open source (OFL license)
- Bundled with app for consistent experience

**Monospace** (for hotkeys, code):
```css
font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
```

### Type Scale

#### H1 - Hero
- **Size:** 48px (3em)
- **Weight:** Bold (700)
- **Line Height:** 1.2
- **Letter Spacing:** -0.5px
- **Use:** Hero headlines, page titles

#### H2 - Section
- **Size:** 40px (2.5em)
- **Weight:** Bold (700)
- **Line Height:** 1.2
- **Letter Spacing:** -0.3px
- **Use:** Major section headings

#### H3 - Subsection
- **Size:** 32px (2em)
- **Weight:** SemiBold (600)
- **Line Height:** 1.3
- **Use:** Subsection headings

#### H4 - Card Title
- **Size:** 24px (1.5em)
- **Weight:** SemiBold (600)
- **Line Height:** 1.4
- **Use:** Card titles, feature headings

#### H5 - Small Heading
- **Size:** 20px (1.25em)
- **Weight:** SemiBold (600)
- **Line Height:** 1.5
- **Use:** Small headings, sidebar titles

#### Body Large
- **Size:** 19px (1.2em)
- **Weight:** Regular (400)
- **Line Height:** 1.6
- **Use:** Hero subheadlines, important body text

#### Body Regular
- **Size:** 16px (1em)
- **Weight:** Regular (400)
- **Line Height:** 1.6
- **Use:** Standard body text, paragraphs

#### Body Small
- **Size:** 14px (0.875em)
- **Weight:** Regular (400)
- **Line Height:** 1.5
- **Use:** Secondary content, sidebars

#### Caption
- **Size:** 13px (0.8125em)
- **Weight:** Regular (400)
- **Line Height:** 1.4
- **Use:** Image captions, footnotes, legal text

#### Button Large
- **Size:** 18px (1.125em)
- **Weight:** SemiBold (600)
- **Letter Spacing:** 0.3px
- **Use:** Primary CTAs, hero buttons

#### Button Regular
- **Size:** 16px (1em)
- **Weight:** SemiBold (600)
- **Letter Spacing:** 0.2px
- **Use:** Standard buttons

### Typography Rules

1. **Max Line Length:** 75 characters for optimal readability
2. **Paragraph Spacing:** 1.5em (24px) between paragraphs
3. **Heading Margins:** 1.5em top, 0.5em bottom
4. **No Mixing Weights:** Don't mix Regular and SemiBold in same paragraph
5. **Alignment:** Left-align body text, center-align headings only when appropriate

### Typography Do's and Don'ts

✅ **DO:**
- Use consistent type scale
- Maintain hierarchy (H1 > H2 > H3)
- Use adequate line height for readability
- Keep body text left-aligned
- Use SemiBold for emphasis instead of Bold in body text

❌ **DON'T:**
- Use more than 3 font weights in a single layout
- Set body text in ALL CAPS (reduces readability)
- Use justified text (creates rivers of white space)
- Set body text smaller than 16px
- Use tight line-height (<1.4) for body text

---

## Iconography

### Icon Style

**Type:** Outline style (not filled)
- Lighter, more approachable than filled icons
- Works well at small sizes
- Consistent with modern UI trends

**Stroke Weight:** 2px at 24×24px base size

**Corners:** Rounded (2px radius) - softer, friendlier than sharp corners

**Grid:** 24×24px base (scales to 16px, 32px, 48px)

**Color:** Inherit from context using `currentColor` in SVG

### Recommended Icon Library

**Option 1: [Lucide Icons](https://lucide.dev)** (Recommended)
- Free, open source
- Outline style, consistent stroke weight
- Excellent React/Vue/Svelte support
- 1000+ icons

**Option 2: [Heroicons](https://heroicons.com)**
- Free, by Tailwind team
- Outline style
- Fewer icons but high quality

**Consistency Rule:** Use same library throughout. Don't mix icon sets.

### Custom Icons Needed

Icons specific to MurmurTone that aren't in libraries:
1. **MurmurTone logo mark** (unique brand icon)
2. **Microphone with waveform** (product-specific)
3. **Lock with sound wave** (privacy + voice combination)
4. **Local processing indicator** (on-device AI symbol)

### Icon Sizing

**In Buttons:**
- Size: 16px or 20px
- Spacing: 8px gap from text

**In Feature Cards:**
- Size: 48px
- Position: Centered above text
- Color: #667eea (brand primary)

**In Navigation:**
- Size: 24px
- Aligned with text

**Inline with Text:**
- Size: 16px
- Vertically centered with text

### Icon Usage

✅ **DO:**
- Use icons to support text, not replace it
- Maintain consistent stroke weight across all icons
- Use color thoughtfully (brand colors for positive actions)
- Ensure icons are accessible (include aria-labels)

❌ **DON'T:**
- Mix outline and filled icon styles
- Use icons without text for critical actions
- Scale icons non-proportionally
- Use low-contrast icons on backgrounds

---

## Brand Voice & Messaging

### Brand Voice Attributes

#### 1. Trustworthy (Primary)
- **Why:** Privacy is core - users must trust MurmurTone with their voice
- **How:** Clear, honest language; no marketing hyperbole; transparent about limitations
- **Example:** "Your voice never leaves your machine" (direct, verifiable)

#### 2. Approachable (Secondary)
- **Why:** Voice typing can be intimidating; need to lower barriers
- **How:** Conversational tone, avoid jargon unless speaking to technical audience
- **Example:** "Press hotkey, speak, release. That's it." (simple, friendly)

#### 3. Efficient (Tertiary)
- **Why:** Target audience values time and productivity
- **How:** Concise copy, bullet points, scannable content
- **Example:** "3x faster than typing" (specific, benefit-focused)

#### 4. Capable (Supporting)
- **Why:** Need to convey technical competence without intimidation
- **How:** Mention technical details when relevant, but don't lead with them
- **Example:** "Powered by faster-whisper" (credibility without complexity)

### What MurmurTone Sounds Like

**Personality:**
- Direct and honest (not clever or witty)
- Confident but not arrogant
- Helpful but not patronizing
- Professional but not corporate/stuffy

**Voice Examples:**

✅ **Good:**
- "Your voice stays on your machine. Period."
- "Fast transcription. Zero tracking. That's our promise."
- "Works offline. Always."
- "Press hotkey, speak, done."

❌ **Avoid:**
- "Revolutionizing voice input forever!" (hyperbolic, salesy)
- "Say goodbye to typing!" (unrealistic promise)
- "Leveraging cutting-edge AI paradigms..." (jargony, pretentious)
- "The world's best voice-to-text!" (unprovable, arrogant)

### Key Messages

#### Primary Message (Lead with this)
**"100% offline voice-to-text that respects your privacy"**

#### Secondary Messages (Supporting points)
1. "Your voice never leaves your machine - all processing happens locally"
2. "Fast, accurate transcription with no internet dependency"
3. "$49/year - 52% less than competitors"

#### Tertiary Messages (Proof points)
1. "Powered by OpenAI Whisper via faster-whisper"
2. "Local AI text cleanup with Ollama integration"
3. "Translation mode for 18+ languages"
4. "Customizable models from speed to accuracy"

### Message Framework by Audience

#### Privacy-Conscious Users
- **Lead:** Privacy (offline processing, zero tracking)
- **Support:** Security (no cloud), Control (own your data)
- **Proof:** Technical architecture, Transparent practices

#### Busy Professionals
- **Lead:** Speed (3x faster, instant transcription)
- **Support:** Reliability (no internet), Efficiency (hotkey workflow)
- **Proof:** Time saved, Seamless integration

#### Developers/Technical Users
- **Lead:** Control (customizable models, open architecture)
- **Support:** Privacy (offline), Technical capability (faster-whisper, CUDA)
- **Proof:** GitHub repo, Technical docs, Model comparisons

#### Budget-Conscious Users
- **Lead:** Value ($49/year vs $96-180)
- **Support:** Lock in forever pricing, No hidden costs
- **Proof:** Feature comparison table

### Positioning Statements

#### Elevator Pitch (30 seconds)
"MurmurTone is offline voice-to-text software for Windows that respects your privacy. Press a hotkey, speak, and your words appear instantly - no cloud, no tracking, no delays. At $49/year, it's half the price of competitors while being the only tool offering local AI text cleanup. Your voice stays on your machine, always."

#### One-Sentence Positioning
"MurmurTone is the privacy-first voice-to-text app for Windows that processes everything offline at half the cost of cloud competitors."

### Writing Guidelines

#### Sentence Structure
- **Short sentences:** Average 15-20 words
- **Active voice:** "MurmurTone transcribes your voice" not "Your voice is transcribed"
- **Simple words:** "Use" not "utilize", "Help" not "facilitate"

#### Formatting
- **Bullet points:** For scannable lists
- **Bold for emphasis:** Sparingly, for key points only
- **Numbers:** Specific benefits ("3x faster" not "much faster")

#### Tone Modulation

**Marketing/Landing Page:** Confident, benefit-focused
- "Fast, private transcription. No cloud required."

**Documentation:** Helpful, clear, step-by-step
- "To change your hotkey: 1. Right-click the tray icon. 2. Click Settings. 3. Click 'Set Hotkey'."

**Error Messages:** Honest, solution-focused
- "Transcription failed. Check that your microphone is connected and try again."

**Social Media:** Approachable, educational, transparent
- "Privacy tip: Your voice data is valuable. That's why MurmurTone never uploads it anywhere."

---

## Visual Design System

### Spacing System

**Base Unit:** 4px

All spacing should be multiples of 4px for visual consistency.

**Spacing Scale:**
- **xs:** 4px (0.25rem) - Icon spacing, tight elements
- **sm:** 8px (0.5rem) - Button padding vertical, compact spacing
- **md:** 16px (1rem) - Default spacing, component gaps
- **lg:** 24px (1.5rem) - Section padding, card spacing
- **xl:** 32px (2rem) - Section margins
- **2xl:** 48px (3rem) - Major section gaps
- **3xl:** 64px (4rem) - Hero sections, major breaks
- **4xl:** 96px (6rem) - Page section dividers

### Layout Grid

**Container System:**
- **Max Width:**
  - Landing pages: 1000px
  - Install page: 800px
  - Documentation: 1200px
- **Side Padding:**
  - Mobile: 20px
  - Tablet+: 40px

**Breakpoints:**
- **Mobile:** 0-768px (single column)
- **Tablet:** 768-1024px (2 columns)
- **Desktop:** 1024px+ (3-4 columns)

**Grid System:**
- 12-column grid for flexibility
- Feature cards: 3-column desktop, 2-column tablet, 1-column mobile
- Grid gap: 40px desktop, 30px tablet, 20px mobile

### Elevation (Shadows)

```css
/* Subtle borders and light elevation */
box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);

/* Cards, modals - standard elevation */
box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);

/* Floating elements, hover states - higher elevation */
box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);

/* Branded elements with purple tint */
box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
```

**Usage:**
- **Cards:** 0 4px 20px rgba(0, 0, 0, 0.1)
- **Buttons (hover):** 0 10px 25px rgba(0, 0, 0, 0.2)
- **Modals/Dialogs:** 0 10px 25px rgba(0, 0, 0, 0.2)
- **Branded CTAs (hover):** 0 10px 25px rgba(102, 126, 234, 0.3)

### Border Radius

- **none:** 0px - Tables, strict layouts
- **sm:** 4px - Form inputs, small buttons
- **md:** 6px - Buttons, small cards
- **lg:** 8px - Images, medium cards
- **xl:** 12px - Hero cards, major sections
- **full:** 9999px - Pills, tags, circular elements

**Component Assignments:**
- Buttons: 6px (md)
- Cards: 12px (xl)
- Input fields: 4px (sm)
- Images: 8px (lg)
- Badges/tags: 9999px (full)

### Component Library

#### Buttons

**Primary CTA**
```css
.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 14px 40px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 1.1em;
  border: none;
  cursor: pointer;
  transition: transform 0.3s ease-out, box-shadow 0.3s ease-out;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}
```

**Secondary CTA**
```css
.btn-secondary {
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
  padding: 12px 38px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s ease-out;
}

.btn-secondary:hover {
  background: #f5f5f5;
}
```

**Ghost Button**
```css
.btn-ghost {
  background: transparent;
  color: #667eea;
  padding: 14px 40px;
  border-radius: 6px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: background 0.3s ease-out;
}

.btn-ghost:hover {
  background: rgba(102, 126, 234, 0.1);
}
```

#### Cards

**Standard Card**
```css
.card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 40px;
  transition: transform 0.3s ease-out, box-shadow 0.3s ease-out;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
}
```

**Flat Card (No Shadow)**
```css
.card-flat {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 20px;
}
```

#### Form Inputs

```css
.input {
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
  font-family: inherit;
  transition: border-color 0.3s ease-out, box-shadow 0.3s ease-out;
}

.input:focus {
  border-color: #667eea;
  outline: none;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}
```

#### Feature Cards

```css
.feature-card {
  text-align: center;
  padding: 30px 20px;
}

.feature-icon {
  font-size: 48px; /* or 48×48px SVG */
  margin-bottom: 15px;
  color: #667eea;
}

.feature-title {
  font-size: 1.3em;
  font-weight: 600;
  margin-bottom: 10px;
  color: #222;
}

.feature-description {
  color: #666;
  line-height: 1.8;
}
```

#### Comparison Tables

```css
.comparison-table {
  width: 100%;
  border-collapse: collapse;
}

.comparison-table th {
  background: #f5f5f5;
  padding: 15px;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid #ddd;
}

.comparison-table td {
  padding: 15px;
  border-bottom: 1px solid #eee;
}

.comparison-table tr:nth-child(even) {
  background: #fafafa;
}

.checkmark {
  color: #667eea;
  font-weight: bold;
}

.xmark {
  color: #ccc;
}
```

### Animation Principles

**Timing:**
- Fast interactions: 0.15s (hover, active states)
- Standard transitions: 0.3s (buttons, cards)
- Modal/dialog: 0.4s (entrance/exit)
- Page transitions: 0.6s (if used)

**Easing:**
- Entrance animations: `ease-out` (accelerate out, slow at end)
- Exit animations: `ease-in` (slow start, accelerate out)
- Standard: `ease-in-out` (smooth both ways)

**Common Animation Patterns:**
```css
/* Hover lift */
.element {
  transition: transform 0.3s ease-out;
}
.element:hover {
  transform: translateY(-2px);
}

/* Fade in */
.fade-in {
  opacity: 0;
  animation: fadeIn 0.4s ease-in forwards;
}
@keyframes fadeIn {
  to { opacity: 1; }
}

/* Slide up */
.slide-up {
  transform: translateY(20px);
  animation: slideUp 0.4s ease-out forwards;
}
@keyframes slideUp {
  to { transform: translateY(0); }
}
```

---

## Website Guidelines

### Page Structure

All pages should follow this structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Title | MurmurTone</title>
  <!-- Meta tags, CSS -->
</head>
<body>
  <header><!-- Logo, navigation --></header>
  <main><!-- Page content --></main>
  <footer><!-- Footer links, copyright --></footer>
</body>
</html>
```

### Header

**Standard Header (all pages):**
- Logo: Full logo (icon + wordmark) on left
- Navigation: Right-aligned
  - Features
  - Pricing
  - Docs
  - Support
  - Download (CTA button)
- Mobile: Hamburger menu

### Footer

**Standard Footer (all pages):**
- **Column 1: Product**
  - Features
  - Pricing
  - Download
  - Changelog

- **Column 2: Resources**
  - Documentation
  - Tutorials
  - Support
  - FAQ

- **Column 3: Company**
  - About
  - Contact
  - GitHub
  - Blog (if exists)

- **Column 4: Legal**
  - Privacy Policy
  - Terms of Service
  - License (MIT)

**Footer Bottom:**
- Copyright: "© 2026 MurmurTone. Privacy-focused speech recognition."
- Social links: GitHub, Twitter (if exists)

### Responsive Breakpoints

**Mobile (<768px):**
- Single column layout
- Full-width buttons
- Hamburger navigation
- Font sizes: 85% of desktop

**Tablet (768px-1024px):**
- 2-column grid for features
- Side padding: 30px
- Font sizes: 90% of desktop

**Desktop (1024px+):**
- 3-4 column grid for features
- Side padding: 40px
- Full typography scale

### Call-to-Action Best Practices

1. **Primary CTA:** Use gradient button style, prominent placement
2. **One primary CTA per section:** Don't compete for attention
3. **Clear action words:** "Start Free Trial", "Download Now", not "Click Here"
4. **Trust indicators:** "No credit card required", "14-day trial"
5. **Consistent placement:** Top right header, end of sections

---

## Email Guidelines

### Email Template Structure

**Header:**
- Plain text: "MurmurTone"
- HTML: Logo image (hosted)

**Body:**
- Greeting: "Hi [Name],"
- Clear sections with whitespace
- Bullet points for scannable content
- Single clear CTA

**Footer:**
- "Your voice, locally."
- Unsubscribe link
- Privacy policy link
- Contact email

### Email Types

#### 1. Transactional
- Welcome (trial start)
- Trial expiring (day 12)
- License activation
- Password reset (if accounts exist)

#### 2. Marketing
- Feature announcements
- Tips & tricks
- Blog post notifications (if blog exists)

### Email Design

**Plain Text (Preferred):**
```
Subject: Welcome to MurmurTone

Hi [Name],

Welcome! Your 14-day trial is active.

Getting Started:
• Launch MurmurTone (system tray)
• Right-click → Settings
• Press hotkey, speak, release

Need help? murmurtone.com/docs

Your voice, locally.
- The MurmurTone Team

---
Unsubscribe | Privacy Policy
```

**HTML (Optional):**
- Single-column layout (600px max width)
- Minimal gradient (header only)
- System font stack
- Large, tappable buttons (44px min height)
- Alt text for all images

### Email Best Practices

1. **Subject Lines:** Clear, concise, <50 characters
2. **Preview Text:** First sentence should be engaging
3. **Personalization:** Use name if available
4. **Mobile-First:** 46% of emails opened on mobile
5. **Plain Text Version:** Always include (accessibility, spam filters)

---

## Social Media Guidelines

### Platform Strategy

**Primary Platforms:**
1. **Twitter/X** - Developer community, privacy advocates
2. **GitHub** - Open source community, technical users
3. **Reddit** - r/privacy, r/Windows, r/productivity

**Secondary:**
4. **LinkedIn** - Professional users, future B2B
5. **YouTube** - Tutorial videos, feature demos (post-launch)

### Profile Setup

**Profile Picture:**
- Logo icon (square)
- Size: 400×400px minimum
- Format: PNG with transparency

**Cover/Banner:**
- Gradient background
- MurmurTone logo on left
- Tagline: "Your voice, locally."
- Key visual: Waveform or privacy shield
- Sizes:
  - Twitter: 1500×500px
  - LinkedIn: 1584×396px
  - Facebook: 820×312px

**Bio/About:**
```
MurmurTone - Private voice-to-text for Windows

100% offline transcription
No cloud, no tracking
$49/year

Your voice, locally. 🎤

murmurtone.com
```

### Content Pillars

**Privacy (40%):**
- Privacy tips and education
- Benefits of offline processing
- Data sovereignty content
- Security comparisons

**Product Updates (30%):**
- New features
- Tutorials and how-tos
- Tips for better transcription
- Behind-the-scenes development

**Productivity (20%):**
- Voice typing workflows
- Time-saving tips
- Integration ideas
- User productivity stories

**Community (10%):**
- User testimonials
- Feature requests discussion
- Community support
- User-generated content

### Posting Guidelines

**Tone:**
- Direct and helpful
- Transparent and honest
- Educational, not promotional

**Avoid:**
- Hype and marketing-speak
- Overselling or exaggeration
- Attacking competitors
- Engagement bait

**Do:**
- Share technical details
- Be honest about limitations
- Respond to user feedback
- Educate about privacy

**Hashtags:**
- #Privacy
- #VoiceTyping
- #OfflineFirst
- #Windows
- #Productivity
- #LocalAI

### Visual Content for Social

**Screenshots:**
- Clean, uncluttered
- Highlight single feature
- Annotate with arrows/callouts
- Maintain brand colors

**Graphics:**
- Purple-blue gradient backgrounds
- White text
- Feature icons from icon library
- Consistent style across all graphics

**Videos:**
- Screen recordings with voiceover
- No background music (ironic for voice app)
- Short (<60 seconds)
- Clear, step-by-step
- Closed captions for accessibility

---

## Visual Expression

### Core Brand Attributes (Visual)

#### Privacy
- **Visual:** Lock icons, shield imagery, contained shapes
- **Color:** Darker purple (#5a3875), charcoal (#222)
- **Imagery:** Local/on-device visuals, desktop screenshots, NO cloud imagery

#### Simplicity
- **Visual:** Clean layouts, generous whitespace, minimal elements
- **Color:** Light backgrounds, subtle grays, off-white
- **Imagery:** Uncluttered screenshots, simple diagrams

#### Speed
- **Visual:** Sleek lines, dynamic angles, quick animations
- **Color:** Bright gradient, indigo primary
- **Imagery:** Waveforms, lightning bolt icons, motion blur (sparingly)

#### Trustworthy
- **Visual:** Balanced layouts, professional polish, real screenshots
- **Color:** Consistent palette, no jarring colors
- **Imagery:** Real product screenshots (not mockups), honest representations

### Visual Do's and Don'ts

✅ **DO:**
- Use gradient for hero sections and primary CTAs
- Show real MurmurTone product screenshots
- Use lock/shield icons for privacy messaging
- Keep backgrounds light and clean
- Use whitespace generously
- Maintain consistent icon style (outline, rounded)
- Use purple-blue colors for all brand elements
- Show offline/local indicators prominently

❌ **DON'T:**
- Use cloud imagery (contradicts offline message)
- Overuse gradient (dilutes impact - hero + CTAs only)
- Use stock photos of people (not authentic for privacy brand)
- Use neon/bright colors outside approved palette
- Create busy, cluttered layouts
- Mix icon styles (outline vs filled)
- Use abstract/unclear imagery
- Show network/connectivity graphics

### Photography & Imagery

**Preferred Imagery:**
1. **Product Screenshots:** Real MurmurTone interface (settings, preview, transcription)
2. **Icons:** Lucide/Heroicons library + custom MurmurTone icons
3. **Diagrams:** Simple flow diagrams for features (clean, minimal)
4. **Waveforms:** Audio visualizations (brand-appropriate)

**Avoid:**
1. Stock photos of people (not authentic)
2. Generic tech imagery (unless specific context)
3. Cloud/network graphics (contradicts message)
4. Overly abstract imagery (confusing)

**Image Treatment:**
- Border radius: 8px for screenshots
- Shadow: 0 4px 20px rgba(0, 0, 0, 0.1)
- Captions: Below image, 14px gray text
- Max width: 800px (readability)
- Alt text: Descriptive for accessibility

---

## Usage Examples

### Good Example: Feature Card

```html
<div class="feature-card">
  <div class="feature-icon">🔒</div>
  <h3 class="feature-title">100% Offline</h3>
  <p class="feature-description">
    Your voice never leaves your machine. Process everything
    locally with zero internet dependency.
  </p>
</div>
```

**Why it works:**
- Clear icon (lock = privacy)
- Concise title (3 words)
- Benefit-focused description
- Brand voice (direct, honest)

### Good Example: CTA Section

```html
<section class="cta-section">
  <h2>Ready to Take Back Your Privacy?</h2>
  <p>Try MurmurTone free for 14 days. No credit card required.</p>
  <p class="pricing">$49/year — Early Access Pricing</p>
  <a href="/install" class="btn-primary">Start Free Trial</a>
</section>
```

**Why it works:**
- Clear value proposition
- Trust indicator (no credit card)
- Transparent pricing
- Action-oriented button text

### Bad Example: Overhyped Copy

❌ "MurmurTone is REVOLUTIONIZING voice input with GAME-CHANGING AI technology that will TRANSFORM your workflow FOREVER!"

**Why it fails:**
- All caps (aggressive, salesy)
- Hyperbolic language (revolutionizing, game-changing)
- Unrealistic promise (forever)
- Not trustworthy or approachable

### Good Example: Error Message

✅ "Transcription failed. Check that your microphone is connected and try again."

**Why it works:**
- Direct and clear
- Actionable solution
- Helpful tone
- No blame or frustration

---

## Version History

**Version 1.0** - January 2026
- Initial brand guide release
- Colors, typography, logo, voice, visual system defined
- Website, email, social media guidelines
- Component library and spacing system

---

## Questions or Feedback?

For questions about brand guidelines or to suggest updates:
- **Email:** brand@murmurtone.com (if it exists)
- **GitHub:** [Open an issue](https://github.com/tuckerandrew21/murmurtone/issues)
- **Internal:** Contact the marketing/brand team

---

**Remember:** Consistency builds trust. Follow these guidelines to maintain a cohesive brand experience across all touchpoints.

**MurmurTone** - Your voice, locally. 🎤
